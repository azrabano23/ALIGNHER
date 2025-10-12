"""
Example integration code for Phase 1 scheduling system
This shows how your friend's system should call your no-show prevention API
"""

import requests
import json
from datetime import datetime

# Your no-show prevention system URL
NOSHOW_API_URL = "http://localhost:8000"  # Update with your actual URL
API_KEY = "your-api-key-here"  # For authentication

class NoShowIntegration:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def create_appointment_with_noshow_prevention(self, appointment_data: dict):
        """
        Call this from Phase 1 system after creating an appointment
        """
        
        # Transform Phase 1 data to Phase 2 format
        noshow_payload = {
            "external_id": appointment_data["appointment_id"],
            "patient_external_id": appointment_data["patient_id"],
            "patient_first_name": appointment_data["patient"]["first_name"],
            "patient_last_name": appointment_data["patient"]["last_name"],
            "patient_phone": appointment_data["patient"]["phone"],
            "patient_email": appointment_data["patient"]["email"],
            "patient_date_of_birth": appointment_data["patient"]["date_of_birth"],
            
            "provider_external_id": appointment_data["provider_id"],
            "provider_name": appointment_data["provider"]["name"],
            "provider_specialty": appointment_data["provider"]["specialty"],
            "provider_location": appointment_data["provider"]["location"],
            
            "appointment_datetime": appointment_data["appointment_datetime"],
            "appointment_type": appointment_data["appointment_type"],
            "duration_minutes": appointment_data["duration_minutes"],
            
            # Critical: Pass triage data from Phase 1
            "chief_complaint": appointment_data["triage"]["chief_complaint"],
            "clinical_priority": appointment_data["triage"]["priority_level"],  # red/orange/yellow/green
            "triage_notes": appointment_data["triage"]["notes"]
        }
        
        try:
            # Call your no-show prevention system
            response = requests.post(
                f"{self.api_url}/api/v1/appointments",
                json=noshow_payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ No-show prevention activated for appointment {result['id']}")
                return result
            else:
                print(f"❌ No-show API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Integration error: {e}")
            return None

# Example usage in Phase 1 system
def example_phase1_workflow():
    """
    Example of how Phase 1 system integrates with Phase 2
    """
    
    # 1. Phase 1: Patient calls, VCC does triage
    triage_result = {
        "chief_complaint": "Postmenopausal bleeding",
        "priority_level": "red",  # High priority from triage
        "notes": "Urgent gynecology referral needed",
        "recommended_specialty": "gynecology",
        "recommended_timeframe": "7-10 days"
    }
    
    # 2. Phase 1: System finds available provider and books appointment
    appointment_data = {
        "appointment_id": "APPT_12345",
        "patient_id": "PAT_67890",
        "patient": {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+1234567890",
            "email": "jane.smith@email.com",
            "date_of_birth": "1965-03-15T00:00:00"
        },
        "provider_id": "PROV_001",
        "provider": {
            "name": "Dr. Johnson",
            "specialty": "Gynecology",
            "location": "Women's Health Center"
        },
        "appointment_datetime": "2025-10-18T14:30:00",
        "appointment_type": "new_patient",
        "duration_minutes": 45,
        "triage": triage_result
    }
    
    # 3. Phase 1: Immediately call Phase 2 for no-show prevention
    noshow_integration = NoShowIntegration(NOSHOW_API_URL, API_KEY)
    noshow_result = noshow_integration.create_appointment_with_noshow_prevention(appointment_data)
    
    if noshow_result:
        print(f"🎯 Risk assessment: {noshow_result.get('risk_tier', 'pending')}")
        print("📱 Interventions will be automatically triggered")
    
    return appointment_data

if __name__ == "__main__":
    example_phase1_workflow()
