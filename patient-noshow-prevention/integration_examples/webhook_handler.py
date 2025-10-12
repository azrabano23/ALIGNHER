"""
Webhook handler for Phase 1 system integration
Add this to your main.py to receive webhooks from Phase 1
"""

from fastapi import HTTPException
from app.schemas import Phase1AppointmentWebhook
import logging

logger = logging.getLogger(__name__)

# Add this endpoint to your main.py
@app.post("/webhooks/phase1/appointment")
async def handle_phase1_webhook(
    webhook_data: Phase1AppointmentWebhook,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle webhooks from Phase 1 scheduling system
    """
    try:
        logger.info(f"Received Phase 1 webhook: {webhook_data.event_type}")
        
        if webhook_data.event_type == "appointment_created":
            # Create appointment in your system
            appointment_response = await create_appointment(
                webhook_data.appointment_data,
                background_tasks,
                db
            )
            
            return {
                "status": "success",
                "message": "Appointment processed for no-show prevention",
                "appointment_id": appointment_response.id
            }
            
        elif webhook_data.event_type == "appointment_updated":
            # Update existing appointment
            # Find appointment by external_id and update
            appointment = db.query(Appointment).filter(
                Appointment.external_id == webhook_data.appointment_id
            ).first()
            
            if appointment:
                # Update appointment details
                # Re-assess risk if needed
                background_tasks.add_task(assess_and_trigger_interventions, appointment.id, db)
                
            return {"status": "success", "message": "Appointment updated"}
            
        elif webhook_data.event_type == "appointment_cancelled":
            # Cancel interventions
            appointment = db.query(Appointment).filter(
                Appointment.external_id == webhook_data.appointment_id
            ).first()
            
            if appointment:
                # Cancel pending interventions
                db.query(Intervention).filter(
                    Intervention.appointment_id == appointment.id,
                    Intervention.status == InterventionStatus.PENDING
                ).update({"status": InterventionStatus.FAILED})
                db.commit()
                
            return {"status": "success", "message": "Interventions cancelled"}
        
        else:
            return {"status": "ignored", "message": f"Unknown event type: {webhook_data.event_type}"}
            
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
