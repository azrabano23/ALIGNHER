import os
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Intervention, Appointment, InterventionStatus
from app.services.intervention_engine import InterventionEngine
from app.services.communication_hub import communication_hub
from app.ml.risk_predictor import risk_predictor
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "patient_noshow_prevention",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379")
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "process_pending_interventions": {
            "task": "app.tasks.process_pending_interventions",
            "schedule": 60.0,  # Run every minute
        },
        "retrain_model": {
            "task": "app.tasks.retrain_model",
            "schedule": 24 * 60 * 60.0,  # Run daily
        },
        "cleanup_old_data": {
            "task": "app.tasks.cleanup_old_data",
            "schedule": 7 * 24 * 60 * 60.0,  # Run weekly
        }
    }
)

@celery_app.task
def execute_intervention(intervention_id: int):
    """
    Execute a specific intervention
    """
    db = SessionLocal()
    try:
        intervention_engine = InterventionEngine(db, communication_hub)
        result = intervention_engine.execute_intervention(intervention_id)
        
        logger.info(f"Intervention {intervention_id} executed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute intervention {intervention_id}: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def process_pending_interventions():
    """
    Process all pending interventions that are due
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Get all pending interventions that are due
        pending_interventions = db.query(Intervention).filter(
            Intervention.status == InterventionStatus.PENDING,
            Intervention.scheduled_at <= now
        ).all()
        
        logger.info(f"Processing {len(pending_interventions)} pending interventions")
        
        for intervention in pending_interventions:
            # Execute intervention asynchronously
            execute_intervention.delay(intervention.id)
        
        return {"processed": len(pending_interventions)}
        
    except Exception as e:
        logger.error(f"Failed to process pending interventions: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def assess_appointment_risk(appointment_id: int):
    """
    Assess risk for an appointment and trigger interventions
    """
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()
        
        if not appointment:
            logger.error(f"Appointment {appointment_id} not found")
            return {"status": "failed", "error": "Appointment not found"}
        
        # Prepare data for ML model
        appointment_data = {
            'appointment_datetime': appointment.appointment_datetime,
            'appointment_type': appointment.appointment_type,
            'duration_minutes': appointment.duration_minutes,
            'clinical_priority': appointment.clinical_priority.value if appointment.clinical_priority else 'green',
            'patient': {
                'date_of_birth': appointment.patient.date_of_birth,
                'total_appointments': appointment.patient.total_appointments,
                'no_show_count': appointment.patient.no_show_count,
                'cancellation_count': appointment.patient.cancellation_count,
                'last_appointment_date': appointment.patient.last_appointment_date
            },
            'provider': {
                'specialty': appointment.provider.specialty,
                'average_no_show_rate': appointment.provider.average_no_show_rate
            },
            'risk_profile': {}
        }
        
        # Get risk prediction
        if risk_predictor.is_trained:
            risk_result = risk_predictor.predict_risk(appointment_data)
        else:
            # Simple fallback
            risk_result = {
                'risk_score': 0.3,
                'risk_tier': 'medium',
                'confidence': 0.5,
                'top_risk_factors': []
            }
        
        # Update appointment
        from app.models import RiskTier
        appointment.no_show_risk_score = risk_result['risk_score']
        appointment.risk_tier = RiskTier(risk_result['risk_tier'])
        appointment.risk_factors = str(risk_result.get('top_risk_factors', []))
        
        db.commit()
        
        # Trigger interventions
        intervention_engine = InterventionEngine(db, communication_hub)
        interventions = intervention_engine.trigger_interventions(appointment_id)
        
        logger.info(f"Risk assessment and intervention setup completed for appointment {appointment_id}")
        
        return {
            "status": "completed",
            "risk_score": risk_result['risk_score'],
            "risk_tier": risk_result['risk_tier'],
            "interventions_created": len(interventions)
        }
        
    except Exception as e:
        logger.error(f"Risk assessment failed for appointment {appointment_id}: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def retrain_model():
    """
    Retrain the ML model with recent data
    """
    db = SessionLocal()
    try:
        # Get training data from completed appointments
        from app.models import AppointmentOutcome
        
        completed_appointments = db.query(Appointment).filter(
            Appointment.outcome.in_([AppointmentOutcome.ATTENDED, AppointmentOutcome.NO_SHOW])
        ).all()
        
        if len(completed_appointments) < 1000:
            logger.info(f"Not enough training data ({len(completed_appointments)} samples), skipping retrain")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        # Prepare training data
        training_data = []
        for appointment in completed_appointments:
            appointment_data = {
                'appointment_datetime': appointment.appointment_datetime,
                'appointment_type': appointment.appointment_type,
                'duration_minutes': appointment.duration_minutes,
                'clinical_priority': appointment.clinical_priority.value if appointment.clinical_priority else 'green',
                'outcome': appointment.outcome.value,
                'patient': {
                    'date_of_birth': appointment.patient.date_of_birth,
                    'total_appointments': appointment.patient.total_appointments,
                    'no_show_count': appointment.patient.no_show_count,
                    'cancellation_count': appointment.patient.cancellation_count,
                    'last_appointment_date': appointment.patient.last_appointment_date
                },
                'provider': {
                    'specialty': appointment.provider.specialty,
                    'average_no_show_rate': appointment.provider.average_no_show_rate
                },
                'risk_profile': {}
            }
            training_data.append(appointment_data)
        
        # Train model
        metrics = risk_predictor.train(training_data)
        
        # Save model performance
        from app.models import ModelPerformance
        
        model_performance = ModelPerformance(
            model_version=f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            auc_roc=metrics['auc_roc'],
            training_samples=metrics['training_samples'],
            feature_importance=str(metrics['feature_importance']),
            is_active=True
        )
        
        # Deactivate old models
        db.query(ModelPerformance).update({'is_active': False})
        
        db.add(model_performance)
        db.commit()
        
        # Save model to disk
        model_path = f"/tmp/noshow_model_{model_performance.model_version}.pkl"
        risk_predictor.save_model(model_path)
        
        logger.info(f"Model retrained successfully: {metrics}")
        
        return {
            "status": "completed",
            "model_version": model_performance.model_version,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def cleanup_old_data():
    """
    Clean up old data to maintain database performance
    """
    db = SessionLocal()
    try:
        # Delete old interventions (older than 6 months)
        cutoff_date = datetime.utcnow() - timedelta(days=180)
        
        old_interventions = db.query(Intervention).filter(
            Intervention.created_at < cutoff_date
        ).count()
        
        db.query(Intervention).filter(
            Intervention.created_at < cutoff_date
        ).delete()
        
        # Delete old model performance records (keep last 10)
        from app.models import ModelPerformance
        
        old_models = db.query(ModelPerformance).order_by(
            ModelPerformance.training_date.desc()
        ).offset(10).all()
        
        for model in old_models:
            db.delete(model)
        
        db.commit()
        
        logger.info(f"Cleaned up {old_interventions} old interventions and {len(old_models)} old models")
        
        return {
            "status": "completed",
            "interventions_deleted": old_interventions,
            "models_deleted": len(old_models)
        }
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def send_daily_report():
    """
    Send daily performance report
    """
    db = SessionLocal()
    try:
        # Calculate daily stats
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Get appointments from yesterday
        from sqlalchemy import func, and_
        
        yesterday_appointments = db.query(Appointment).filter(
            func.date(Appointment.appointment_datetime) == yesterday
        ).all()
        
        total_appointments = len(yesterday_appointments)
        no_shows = len([a for a in yesterday_appointments if a.outcome and a.outcome.value == 'no_show'])
        attended = len([a for a in yesterday_appointments if a.outcome and a.outcome.value == 'attended'])
        
        no_show_rate = no_shows / total_appointments if total_appointments > 0 else 0
        
        # Get intervention stats
        interventions_sent = db.query(Intervention).filter(
            func.date(Intervention.executed_at) == yesterday,
            Intervention.delivered == True
        ).count()
        
        report = {
            "date": yesterday.isoformat(),
            "total_appointments": total_appointments,
            "attended": attended,
            "no_shows": no_shows,
            "no_show_rate": no_show_rate,
            "interventions_sent": interventions_sent
        }
        
        logger.info(f"Daily report: {report}")
        
        # TODO: Send report via email to administrators
        
        return report
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
