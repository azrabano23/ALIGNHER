"""
Sample integration code for Phase 1 developer
Copy and adapt this code into your Phase 1 scheduling system
"""

import requests
import logging
from datetime import datetime
from typing import Dict, Optional
import os
from dataclasses import dataclass

# Configuration
NOSHOW_API_URL = os.getenv("NOSHOW_API_URL", "http://localhost:8000")
NOSHOW_API_KEY = os.getenv("NOSHOW_API_KEY", "your-api-key")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Patient:
    id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    date_of_birth: datetime = None

@dataclass
class Provider:
    id: str
    name: str
    specialty: str
    location: str = None

@dataclass
class TriageData:
    chief_complaint: str
    priority_level: str  # "red", "orange", "yellow", "green"
    notes: str = ""

@dataclass
class Appointment:
    id: str
    patient: Patient
    provider: Provider
    datetime: datetime
    type: str  # "new_patient", "follow_up", "procedure"
    duration: int = 30

class NoShowIntegration:
    """
    Integration class for Phase 1 system
    """
    
    def __init__(self, api_url: str = NOSHOW_API_URL, api_key: str = NOSHOW_API_KEY):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def is_healthy(self) -> bool:
        """Check if no-show prevention system is running"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"No-show system health check failed: {e}")
            return False
    
    def send_appointment(self, appointment: Appointment, triage: TriageData) -> Optional[Dict]:
        """
        Send appointment to no-show prevention system
        
        Args:
            appointment: Appointment object with patient, provider, datetime info
            triage: Triage data with priority and chief complaint
            
        Returns:
            Dict with response data if successful, None if failed
        """
        
        # Don't block if system is down
        if not self.is_healthy():
            logger.warning("No-show system is down, skipping integration")
            return None
        
        try:
            payload = {
                # Appointment identifiers
                "external_id": appointment.id,
                "appointment_datetime": appointment.datetime.isoformat(),
                "appointment_type": appointment.type,
                "duration_minutes": appointment.duration,
                
                # Patient information
                "patient_external_id": appointment.patient.id,
                "patient_first_name": appointment.patient.first_name,
                "patient_last_name": appointment.patient.last_name,
                "patient_phone": appointment.patient.phone,
                "patient_email": appointment.patient.email,
                "patient_date_of_birth": appointment.patient.date_of_birth.isoformat() if appointment.patient.date_of_birth else None,
                
                # Provider information
                "provider_external_id": appointment.provider.id,
                "provider_name": appointment.provider.name,
                "provider_specialty": appointment.provider.specialty,
                "provider_location": appointment.provider.location,
                
                # Triage information (CRITICAL for accuracy)
                "chief_complaint": triage.chief_complaint,
                "clinical_priority": triage.priority_level,
                "triage_notes": triage.notes
            }
            
            response = requests.post(
                f"{self.api_url}/api/v1/appointments",
                json=payload,
                headers=self.headers,
                timeout=10  # Don't wait too long
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ No-show prevention activated for appointment {appointment.id}")
                logger.info(f"   Risk tier: {result.get('risk_tier', 'pending')}")
                return result
            else:
                logger.warning(f"⚠️ No-show API error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning("⚠️ No-show prevention timeout - continuing normally")
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️ Cannot connect to no-show prevention system")
        except Exception as e:
            logger.error(f"❌ No-show integration error: {e}")
        
        return None
    
    def get_appointment_status(self, appointment_id: str) -> Optional[Dict]:
        """Get status of appointment in no-show system"""
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/appointments/{appointment_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Could not get appointment status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return None

# Global integration instance
noshow_integration = NoShowIntegration()

def create_appointment_with_noshow_prevention(
    patient: Patient,
    provider: Provider,
    appointment_datetime: datetime,
    appointment_type: str,
    triage: TriageData,
    duration: int = 30
) -> Appointment:
    """
    Main function to create appointment with no-show prevention
    
    IMPORTANT: This should be called AFTER you've successfully created
    the appointment in your own system.
    """
    
    # Create appointment object
    appointment = Appointment(
        id=f"APPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # Generate ID
        patient=patient,
        provider=provider,
        datetime=appointment_datetime,
        type=appointment_type,
        duration=duration
    )
    
    try:
        # 1. CREATE APPOINTMENT IN YOUR SYSTEM FIRST
        # your_system.create_appointment(appointment)  # Your existing code
        
        # 2. Send to no-show prevention system (secondary)
        noshow_result = noshow_integration.send_appointment(appointment, triage)
        
        # 3. Optionally store the integration result
        if noshow_result:
            # You might want to store this in your database
            appointment.noshow_prevention_id = noshow_result.get('id')
            logger.info(f"Appointment {appointment.id} integrated with no-show prevention")
        
        return appointment
        
    except Exception as e:
        # CRITICAL: Don't let integration errors break appointment creation
        logger.error(f"Appointment creation error: {e}")
        # Still return the appointment even if integration failed
        return appointment

# Example usage functions
def example_urgent_appointment():
    """Example: High-priority appointment (red)"""
    
    patient = Patient(
        id="PAT_001",
        first_name="Jane",
        last_name="Smith",
        phone="+1234567890",
        email="jane.smith@email.com",
        date_of_birth=datetime(1965, 3, 15)
    )
    
    provider = Provider(
        id="PROV_001",
        name="Dr. Johnson",
        specialty="Gynecology",
        location="Women's Health Center"
    )
    
    triage = TriageData(
        chief_complaint="Postmenopausal bleeding",
        priority_level="red",  # HIGH PRIORITY
        notes="Urgent gynecology referral needed, patient concerned about symptoms"
    )
    
    appointment = create_appointment_with_noshow_prevention(
        patient=patient,
        provider=provider,
        appointment_datetime=datetime(2025, 10, 18, 14, 30),
        appointment_type="new_patient",
        triage=triage,
        duration=45
    )
    
    print(f"Created urgent appointment: {appointment.id}")
    return appointment

def example_routine_appointment():
    """Example: Routine appointment (green)"""
    
    patient = Patient(
        id="PAT_002",
        first_name="John",
        last_name="Doe",
        phone="+1987654321",
        email="john.doe@email.com"
    )
    
    provider = Provider(
        id="PROV_002",
        name="Dr. Williams",
        specialty="Internal Medicine",
        location="Main Clinic"
    )
    
    triage = TriageData(
        chief_complaint="Annual physical exam",
        priority_level="green",  # LOW PRIORITY
        notes="Routine annual checkup, no acute concerns"
    )
    
    appointment = create_appointment_with_noshow_prevention(
        patient=patient,
        provider=provider,
        appointment_datetime=datetime(2025, 11, 15, 10, 0),
        appointment_type="follow_up",
        triage=triage,
        duration=30
    )
    
    print(f"Created routine appointment: {appointment.id}")
    return appointment

def check_integration_status():
    """Check if integration is working"""
    
    print("🔍 Checking No-Show Prevention Integration Status")
    print("=" * 50)
    
    # Health check
    if noshow_integration.is_healthy():
        print("✅ No-show prevention system is running")
    else:
        print("❌ No-show prevention system is down")
        return
    
    # Create test appointments
    print("\n📋 Creating test appointments...")
    
    urgent_appt = example_urgent_appointment()
    routine_appt = example_routine_appointment()
    
    # Check status after a moment
    import time
    time.sleep(2)
    
    print(f"\n📊 Checking appointment statuses...")
    
    urgent_status = noshow_integration.get_appointment_status(urgent_appt.id)
    if urgent_status:
        risk = urgent_status.get('risk_assessment', {})
        print(f"Urgent appointment - Risk: {risk.get('risk_tier', 'unknown')} ({risk.get('risk_score', 0):.2f})")
    
    routine_status = noshow_integration.get_appointment_status(routine_appt.id)
    if routine_status:
        risk = routine_status.get('risk_assessment', {})
        print(f"Routine appointment - Risk: {risk.get('risk_tier', 'unknown')} ({risk.get('risk_score', 0):.2f})")
    
    print("\n🎉 Integration test completed!")

if __name__ == "__main__":
    # Run integration test
    check_integration_status()
