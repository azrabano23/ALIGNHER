from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Optional
import logging

from app.database import get_db, engine
from app.models import Base, Appointment, Patient, Provider, Intervention, RiskTier
from app.ml.risk_predictor import risk_predictor
from app.services.intervention_engine import InterventionEngine
from app.services.communication_hub import communication_hub
from app.schemas import (
    AppointmentCreate, AppointmentResponse, RiskAssessmentRequest, 
    RiskAssessmentResponse, InterventionTriggerRequest
)

# Create tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Patient No-Show Prevention System",
    description="AI-powered system to predict and prevent patient no-shows",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Patient No-Show Prevention System", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Phase 1 Integration Endpoints
@app.post("/api/v1/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create appointment and trigger risk assessment (called by Phase 1 system)
    """
    try:
        # Create or get patient
        patient = db.query(Patient).filter(
            Patient.external_id == appointment_data.patient_external_id
        ).first()
        
        if not patient:
            patient = Patient(
                external_id=appointment_data.patient_external_id,
                first_name=appointment_data.patient_first_name,
                last_name=appointment_data.patient_last_name,
                phone=appointment_data.patient_phone,
                email=appointment_data.patient_email,
                date_of_birth=appointment_data.patient_date_of_birth
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
        
        # Create or get provider
        provider = db.query(Provider).filter(
            Provider.external_id == appointment_data.provider_external_id
        ).first()
        
        if not provider:
            provider = Provider(
                external_id=appointment_data.provider_external_id,
                name=appointment_data.provider_name,
                specialty=appointment_data.provider_specialty,
                location=appointment_data.provider_location
            )
            db.add(provider)
            db.commit()
            db.refresh(provider)
        
        # Create appointment
        appointment = Appointment(
            external_id=appointment_data.external_id,
            patient_id=patient.id,
            provider_id=provider.id,
            appointment_datetime=appointment_data.appointment_datetime,
            appointment_type=appointment_data.appointment_type,
            duration_minutes=appointment_data.duration_minutes,
            chief_complaint=appointment_data.chief_complaint,
            clinical_priority=appointment_data.clinical_priority,
            triage_notes=appointment_data.triage_notes
        )
        
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        # Trigger risk assessment in background
        background_tasks.add_task(assess_and_trigger_interventions, appointment.id, db)
        
        logger.info(f"Created appointment {appointment.id} for patient {patient.external_id}")
        
        return AppointmentResponse(
            id=appointment.id,
            external_id=appointment.external_id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            provider_name=provider.name,
            appointment_datetime=appointment.appointment_datetime,
            risk_score=None,  # Will be calculated in background
            risk_tier=None,
            status="created"
        )
        
    except Exception as e:
        logger.error(f"Failed to create appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/appointments/{appointment_id}/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_appointment_risk(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """
    Perform risk assessment for an existing appointment
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
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
            'risk_profile': {}  # TODO: Get from patient risk profile
        }
        
        # Get risk prediction
        if risk_predictor.is_trained:
            risk_result = risk_predictor.predict_risk(appointment_data)
        else:
            # Fallback to simple heuristic if model not trained
            risk_result = _simple_risk_heuristic(appointment_data)
        
        # Update appointment with risk assessment
        appointment.no_show_risk_score = risk_result['risk_score']
        appointment.risk_tier = RiskTier(risk_result['risk_tier'])
        appointment.risk_factors = str(risk_result.get('top_risk_factors', []))
        
        db.commit()
        
        logger.info(f"Risk assessment completed for appointment {appointment_id}: {risk_result['risk_tier']} ({risk_result['risk_score']:.3f})")
        
        return RiskAssessmentResponse(
            appointment_id=appointment_id,
            risk_score=risk_result['risk_score'],
            risk_tier=risk_result['risk_tier'],
            confidence=risk_result['confidence'],
            risk_factors=risk_result.get('top_risk_factors', [])
        )
        
    except Exception as e:
        logger.error(f"Risk assessment failed for appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/interventions/trigger")
async def trigger_interventions(
    request: InterventionTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger interventions for an appointment
    """
    try:
        intervention_engine = InterventionEngine(db, communication_hub)
        interventions = intervention_engine.trigger_interventions(request.appointment_id)
        
        return {
            "appointment_id": request.appointment_id,
            "interventions_created": len(interventions),
            "interventions": interventions
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger interventions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/appointments/{appointment_id}")
async def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Get appointment details with risk assessment and interventions
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    interventions = db.query(Intervention).filter(
        Intervention.appointment_id == appointment_id
    ).all()
    
    return {
        "id": appointment.id,
        "external_id": appointment.external_id,
        "patient": {
            "name": f"{appointment.patient.first_name} {appointment.patient.last_name}",
            "phone": appointment.patient.phone,
            "email": appointment.patient.email
        },
        "provider": {
            "name": appointment.provider.name,
            "specialty": appointment.provider.specialty
        },
        "appointment_datetime": appointment.appointment_datetime,
        "appointment_type": appointment.appointment_type,
        "clinical_priority": appointment.clinical_priority.value if appointment.clinical_priority else None,
        "risk_assessment": {
            "risk_score": appointment.no_show_risk_score,
            "risk_tier": appointment.risk_tier.value if appointment.risk_tier else None,
            "risk_factors": appointment.risk_factors
        },
        "interventions": [
            {
                "id": i.id,
                "type": i.intervention_type,
                "status": i.status.value,
                "scheduled_at": i.scheduled_at,
                "executed_at": i.executed_at,
                "delivered": i.delivered
            }
            for i in interventions
        ]
    }

@app.get("/api/v1/analytics/dashboard")
async def get_analytics_dashboard(db: Session = Depends(get_db)):
    """
    Get analytics dashboard data
    """
    # Get basic stats
    total_appointments = db.query(Appointment).count()
    high_risk_appointments = db.query(Appointment).filter(
        Appointment.risk_tier == RiskTier.HIGH
    ).count()
    
    # Get intervention stats
    total_interventions = db.query(Intervention).count()
    delivered_interventions = db.query(Intervention).filter(
        Intervention.delivered == True
    ).count()
    
    return {
        "total_appointments": total_appointments,
        "high_risk_appointments": high_risk_appointments,
        "total_interventions": total_interventions,
        "delivered_interventions": delivered_interventions,
        "delivery_rate": delivered_interventions / total_interventions if total_interventions > 0 else 0
    }

# Webhook endpoints for communication providers
@app.post("/webhooks/twilio/sms")
async def twilio_sms_webhook(webhook_data: dict):
    """Handle Twilio SMS status webhooks"""
    return communication_hub.handle_sms_webhook(webhook_data)

@app.post("/webhooks/sendgrid/email")
async def sendgrid_email_webhook(webhook_data: dict):
    """Handle SendGrid email event webhooks"""
    return communication_hub.handle_email_webhook(webhook_data)

# Background task functions
async def assess_and_trigger_interventions(appointment_id: int, db: Session):
    """
    Background task to assess risk and trigger interventions
    """
    try:
        # Assess risk
        await assess_appointment_risk(appointment_id, db)
        
        # Trigger interventions
        intervention_engine = InterventionEngine(db, communication_hub)
        intervention_engine.trigger_interventions(appointment_id)
        
        logger.info(f"Completed risk assessment and intervention setup for appointment {appointment_id}")
        
    except Exception as e:
        logger.error(f"Background task failed for appointment {appointment_id}: {e}")

def _simple_risk_heuristic(appointment_data: Dict) -> Dict:
    """
    Simple risk assessment heuristic when ML model is not available
    """
    risk_score = 0.3  # Base risk
    
    # Adjust based on patient history
    patient = appointment_data.get('patient', {})
    total_appts = patient.get('total_appointments', 0)
    no_shows = patient.get('no_show_count', 0)
    
    if total_appts > 0:
        historical_rate = no_shows / total_appts
        risk_score = (risk_score + historical_rate) / 2
    
    # Adjust based on clinical priority
    priority = appointment_data.get('clinical_priority', 'green').lower()
    if priority == 'red':
        risk_score *= 0.7  # High priority patients less likely to no-show
    elif priority == 'green':
        risk_score *= 1.2  # Low priority patients more likely to no-show
    
    # Determine tier
    if risk_score < 0.2:
        tier = "low"
    elif risk_score < 0.6:
        tier = "medium"
    else:
        tier = "high"
    
    return {
        'risk_score': risk_score,
        'risk_tier': tier,
        'confidence': 0.7,
        'top_risk_factors': [
            {'factor': 'historical_no_show_rate', 'value': no_shows / max(total_appts, 1), 'importance': 0.8}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
