from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Appointment, Intervention, Patient, RiskTier, InterventionStatus
from app.services.communication_hub import CommunicationHub
import logging
import json

logger = logging.getLogger(__name__)

class InterventionEngine:
    def __init__(self, db: Session, communication_hub: CommunicationHub):
        self.db = db
        self.communication_hub = communication_hub
        
    def trigger_interventions(self, appointment_id: int) -> List[Dict]:
        """
        Trigger appropriate interventions based on appointment risk tier
        """
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()
        
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")
        
        if not appointment.risk_tier:
            raise ValueError(f"Appointment {appointment_id} has no risk assessment")
        
        interventions = []
        
        if appointment.risk_tier == RiskTier.LOW:
            interventions = self._create_low_risk_interventions(appointment)
        elif appointment.risk_tier == RiskTier.MEDIUM:
            interventions = self._create_medium_risk_interventions(appointment)
        elif appointment.risk_tier == RiskTier.HIGH:
            interventions = self._create_high_risk_interventions(appointment)
        
        # Schedule all interventions
        for intervention_data in interventions:
            intervention = self._create_intervention(appointment, intervention_data)
            self._schedule_intervention(intervention)
        
        logger.info(f"Created {len(interventions)} interventions for appointment {appointment_id}")
        return interventions
    
    def _create_low_risk_interventions(self, appointment: Appointment) -> List[Dict]:
        """
        Low-risk patients: Standard automated reminders
        """
        appt_time = appointment.appointment_datetime
        
        interventions = [
            {
                'type': 'sms_reminder',
                'scheduled_at': appt_time - timedelta(days=1),
                'channel': 'sms',
                'template': 'low_risk_reminder',
                'priority': 'low'
            }
        ]
        
        # Add email reminder if patient prefers email
        if appointment.patient.risk_profiles and appointment.patient.risk_profiles[0].prefers_email:
            interventions.append({
                'type': 'email_reminder',
                'scheduled_at': appt_time - timedelta(days=2),
                'channel': 'email',
                'template': 'low_risk_email_reminder',
                'priority': 'low'
            })
        
        return interventions
    
    def _create_medium_risk_interventions(self, appointment: Appointment) -> List[Dict]:
        """
        Medium-risk patients: Digital pre-check-in process
        """
        appt_time = appointment.appointment_datetime
        
        interventions = [
            # Early engagement with pre-check-in
            {
                'type': 'pre_checkin_invitation',
                'scheduled_at': appt_time - timedelta(days=3),
                'channel': 'sms',
                'template': 'pre_checkin_sms',
                'priority': 'medium'
            },
            {
                'type': 'pre_checkin_email',
                'scheduled_at': appt_time - timedelta(days=3),
                'channel': 'email',
                'template': 'pre_checkin_email',
                'priority': 'medium'
            },
            # Cost transparency
            {
                'type': 'cost_estimate',
                'scheduled_at': appt_time - timedelta(days=2),
                'channel': 'email',
                'template': 'cost_estimate_email',
                'priority': 'medium'
            },
            # Final reminder with telehealth option
            {
                'type': 'reminder_with_telehealth',
                'scheduled_at': appt_time - timedelta(hours=24),
                'channel': 'sms',
                'template': 'telehealth_option_sms',
                'priority': 'medium'
            }
        ]
        
        return interventions
    
    def _create_high_risk_interventions(self, appointment: Appointment) -> List[Dict]:
        """
        High-risk patients: High-touch, problem-solving interventions
        """
        appt_time = appointment.appointment_datetime
        
        interventions = [
            # Early personal outreach
            {
                'type': 'human_call',
                'scheduled_at': appt_time - timedelta(days=3),
                'channel': 'voice',
                'template': 'high_risk_confirmation_call',
                'priority': 'high'
            },
            # Educational content for anxiety reduction
            {
                'type': 'educational_content',
                'scheduled_at': appt_time - timedelta(days=2),
                'channel': 'email',
                'template': 'procedure_education_email',
                'priority': 'high'
            },
            # Transportation assistance offer
            {
                'type': 'transportation_offer',
                'scheduled_at': appt_time - timedelta(days=1),
                'channel': 'sms',
                'template': 'transportation_assistance_sms',
                'priority': 'high'
            },
            # Final confirmation call
            {
                'type': 'final_confirmation',
                'scheduled_at': appt_time - timedelta(hours=4),
                'channel': 'voice',
                'template': 'final_confirmation_call',
                'priority': 'high'
            }
        ]
        
        return interventions
    
    def _create_intervention(self, appointment: Appointment, intervention_data: Dict) -> Intervention:
        """
        Create an intervention record in the database
        """
        # Generate personalized message content
        message_content = self._generate_message_content(
            appointment, 
            intervention_data['template']
        )
        
        intervention = Intervention(
            appointment_id=appointment.id,
            intervention_type=intervention_data['type'],
            status=InterventionStatus.PENDING,
            scheduled_at=intervention_data['scheduled_at'],
            target_channel=intervention_data['channel'],
            message_content=message_content
        )
        
        self.db.add(intervention)
        self.db.commit()
        self.db.refresh(intervention)
        
        return intervention
    
    def _schedule_intervention(self, intervention: Intervention):
        """
        Schedule an intervention for execution
        """
        # Use Celery to schedule the intervention
        from app.tasks import execute_intervention
        
        execute_intervention.apply_async(
            args=[intervention.id],
            eta=intervention.scheduled_at
        )
        
        logger.info(f"Scheduled intervention {intervention.id} for {intervention.scheduled_at}")
    
    def _generate_message_content(self, appointment: Appointment, template: str) -> str:
        """
        Generate personalized message content based on template
        """
        patient_name = appointment.patient.first_name
        provider_name = appointment.provider.name
        appt_date = appointment.appointment_datetime.strftime("%B %d, %Y")
        appt_time = appointment.appointment_datetime.strftime("%I:%M %p")
        
        templates = {
            'low_risk_reminder': f"""
Hi {patient_name}! This is a reminder of your appointment with Dr. {provider_name} 
tomorrow at {appt_time}. Please arrive 15 minutes early. Reply STOP to opt out.
            """.strip(),
            
            'low_risk_email_reminder': f"""
Dear {patient_name},

This is a friendly reminder of your upcoming appointment:

Date: {appt_date}
Time: {appt_time}
Provider: Dr. {provider_name}

Please arrive 15 minutes early for check-in. If you need to reschedule, 
please call us at least 24 hours in advance.

Best regards,
Your Healthcare Team
            """.strip(),
            
            'pre_checkin_sms': f"""
Hi {patient_name}! Your appointment with Dr. {provider_name} is in 3 days. 
Complete your pre-check-in to save time: [LINK]. This helps reduce wait times!
            """.strip(),
            
            'pre_checkin_email': f"""
Dear {patient_name},

Your appointment with Dr. {provider_name} is scheduled for {appt_date} at {appt_time}.

To make your visit smoother and reduce wait times, please complete your 
pre-check-in process: [PRE_CHECKIN_LINK]

This includes:
• Updating your insurance information
• Completing intake forms
• Reviewing your medical history

Thank you for helping us serve you better!
            """.strip(),
            
            'cost_estimate_email': f"""
Dear {patient_name},

Your upcoming appointment on {appt_date} with Dr. {provider_name}:

Estimated costs:
• Office visit: $XXX (estimated after insurance)
• Additional procedures (if needed): $XXX

We accept payment plans and can discuss financial assistance options. 
Please don't let cost concerns prevent you from receiving care.

Questions? Call our billing department at (XXX) XXX-XXXX.
            """.strip(),
            
            'telehealth_option_sms': f"""
Hi {patient_name}! Your appointment with Dr. {provider_name} is tomorrow at {appt_time}. 
Can't make it in person? We can switch to a telehealth visit. Reply YES to switch or CONFIRM for in-person.
            """.strip(),
            
            'high_risk_confirmation_call': f"""
Script for staff: "Hi {patient_name}, this is [NAME] from Dr. {provider_name}'s office. 
I'm calling to confirm your appointment on {appt_date} at {appt_time}. 
Do you have any concerns or need any assistance getting to your appointment?"
            """.strip(),
            
            'procedure_education_email': f"""
Dear {patient_name},

Your upcoming appointment on {appt_date} may involve [PROCEDURE_NAME]. 
We want to make sure you feel prepared and comfortable.

What to expect:
• [PROCEDURE_DETAILS]
• Typical duration: [TIME]
• What to bring: [ITEMS]

Educational video: [VIDEO_LINK]
Frequently asked questions: [FAQ_LINK]

Our team is here to answer any questions. Call us at (XXX) XXX-XXXX.
            """.strip(),
            
            'transportation_assistance_sms': f"""
Hi {patient_name}! Your appointment with Dr. {provider_name} is tomorrow. 
Need help getting there? We can provide a ride voucher. Call (XXX) XXX-XXXX or reply RIDE.
            """.strip(),
            
            'final_confirmation_call': f"""
Script for staff: "Hi {patient_name}, this is [NAME] calling to confirm you're still 
planning to attend your appointment with Dr. {provider_name} today at {appt_time}. 
We're looking forward to seeing you!"
            """
        }
        
        return templates.get(template, f"Reminder: Appointment with Dr. {provider_name} on {appt_date} at {appt_time}")
    
    def execute_intervention(self, intervention_id: int) -> Dict:
        """
        Execute a scheduled intervention
        """
        intervention = self.db.query(Intervention).filter(
            Intervention.id == intervention_id
        ).first()
        
        if not intervention:
            raise ValueError(f"Intervention {intervention_id} not found")
        
        if intervention.status != InterventionStatus.PENDING:
            logger.warning(f"Intervention {intervention_id} is not pending, skipping")
            return {'status': 'skipped', 'reason': 'not_pending'}
        
        # Update status
        intervention.status = InterventionStatus.IN_PROGRESS
        intervention.executed_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Execute based on channel
            if intervention.target_channel == 'sms':
                result = self.communication_hub.send_sms(
                    to=intervention.appointment.patient.phone,
                    message=intervention.message_content
                )
            elif intervention.target_channel == 'email':
                result = self.communication_hub.send_email(
                    to=intervention.appointment.patient.email,
                    subject=f"Appointment Reminder - {intervention.appointment.appointment_datetime.strftime('%B %d')}",
                    body=intervention.message_content
                )
            elif intervention.target_channel == 'voice':
                # For voice calls, create a task for staff
                result = self._create_call_task(intervention)
            else:
                raise ValueError(f"Unknown channel: {intervention.target_channel}")
            
            # Update intervention with results
            intervention.delivered = result.get('delivered', False)
            intervention.status = InterventionStatus.COMPLETED if result.get('delivered') else InterventionStatus.FAILED
            intervention.error_message = result.get('error')
            
            self.db.commit()
            
            logger.info(f"Executed intervention {intervention_id}: {result}")
            return result
            
        except Exception as e:
            intervention.status = InterventionStatus.FAILED
            intervention.error_message = str(e)
            self.db.commit()
            
            logger.error(f"Failed to execute intervention {intervention_id}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _create_call_task(self, intervention: Intervention) -> Dict:
        """
        Create a call task for staff (voice interventions)
        """
        # In a real implementation, this would integrate with a call center system
        # For now, we'll just log it as a task
        
        task_data = {
            'patient_name': intervention.appointment.patient.first_name + ' ' + intervention.appointment.patient.last_name,
            'phone': intervention.appointment.patient.phone,
            'script': intervention.message_content,
            'appointment_datetime': intervention.appointment.appointment_datetime.isoformat(),
            'priority': 'high' if intervention.appointment.risk_tier == RiskTier.HIGH else 'medium'
        }
        
        # TODO: Integrate with call center system or create staff task
        logger.info(f"Call task created: {task_data}")
        
        return {'delivered': True, 'task_created': True}
