#!/usr/bin/env python3
"""
Simple test script to verify the no-show prevention system
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict

BASE_URL = "http://localhost:8000"

def test_system():
    """Test the complete system workflow"""
    
    print("🏥 Testing Patient No-Show Prevention System")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ System is healthy")
    else:
        print("❌ System health check failed")
        return
    
    # Test 2: Create appointment
    print("\n2. Creating test appointment...")
    
    appointment_data = {
        "external_id": "APPT_001",
        "patient_external_id": "PAT_001",
        "patient_first_name": "John",
        "patient_last_name": "Doe",
        "patient_phone": "+1234567890",
        "patient_email": "john.doe@example.com",
        "patient_date_of_birth": "1980-01-15T00:00:00",
        "provider_external_id": "PROV_001",
        "provider_name": "Dr. Smith",
        "provider_specialty": "Internal Medicine",
        "provider_location": "Main Clinic",
        "appointment_datetime": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        "appointment_type": "follow_up",
        "duration_minutes": 30,
        "chief_complaint": "Follow-up visit",
        "clinical_priority": "yellow",
        "triage_notes": "Routine follow-up"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/appointments", json=appointment_data)
    
    if response.status_code == 200:
        appointment = response.json()
        appointment_id = appointment["id"]
        print(f"✅ Appointment created with ID: {appointment_id}")
    else:
        print(f"❌ Failed to create appointment: {response.text}")
        return
    
    # Test 3: Get appointment details
    print(f"\n3. Retrieving appointment details...")
    
    response = requests.get(f"{BASE_URL}/api/v1/appointments/{appointment_id}")
    
    if response.status_code == 200:
        appointment_details = response.json()
        print(f"✅ Retrieved appointment details")
        print(f"   Patient: {appointment_details['patient']['name']}")
        print(f"   Provider: {appointment_details['provider']['name']}")
        print(f"   Risk Score: {appointment_details['risk_assessment']['risk_score']}")
        print(f"   Risk Tier: {appointment_details['risk_assessment']['risk_tier']}")
        print(f"   Interventions: {len(appointment_details['interventions'])}")
    else:
        print(f"❌ Failed to retrieve appointment: {response.text}")
        return
    
    # Test 4: Manual risk assessment
    print(f"\n4. Testing manual risk assessment...")
    
    response = requests.post(f"{BASE_URL}/api/v1/appointments/{appointment_id}/risk-assessment")
    
    if response.status_code == 200:
        risk_assessment = response.json()
        print(f"✅ Risk assessment completed")
        print(f"   Risk Score: {risk_assessment['risk_score']:.3f}")
        print(f"   Risk Tier: {risk_assessment['risk_tier']}")
        print(f"   Confidence: {risk_assessment['confidence']:.3f}")
    else:
        print(f"❌ Risk assessment failed: {response.text}")
    
    # Test 5: Trigger interventions
    print(f"\n5. Testing intervention trigger...")
    
    intervention_request = {"appointment_id": appointment_id}
    response = requests.post(f"{BASE_URL}/api/v1/interventions/trigger", json=intervention_request)
    
    if response.status_code == 200:
        intervention_result = response.json()
        print(f"✅ Interventions triggered")
        print(f"   Interventions created: {intervention_result['interventions_created']}")
    else:
        print(f"❌ Failed to trigger interventions: {response.text}")
    
    # Test 6: Analytics dashboard
    print(f"\n6. Testing analytics dashboard...")
    
    response = requests.get(f"{BASE_URL}/api/v1/analytics/dashboard")
    
    if response.status_code == 200:
        analytics = response.json()
        print(f"✅ Analytics retrieved")
        print(f"   Total appointments: {analytics['total_appointments']}")
        print(f"   High risk appointments: {analytics['high_risk_appointments']}")
        print(f"   Total interventions: {analytics['total_interventions']}")
        print(f"   Delivery rate: {analytics['delivery_rate']:.2%}")
    else:
        print(f"❌ Failed to retrieve analytics: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 System test completed successfully!")
    print("\nNext steps:")
    print("1. Configure Twilio and SendGrid credentials in .env")
    print("2. Set up Phase 1 system integration")
    print("3. Start collecting real appointment data for ML training")
    print("4. Deploy to production environment")

def create_sample_data():
    """Create sample data for testing"""
    
    print("\n📊 Creating sample data for testing...")
    
    # Create multiple appointments with different risk profiles
    sample_appointments = [
        {
            "external_id": f"APPT_{i:03d}",
            "patient_external_id": f"PAT_{i:03d}",
            "patient_first_name": f"Patient{i}",
            "patient_last_name": "Test",
            "patient_phone": f"+123456{i:04d}",
            "patient_email": f"patient{i}@example.com",
            "provider_external_id": "PROV_001",
            "provider_name": "Dr. Smith",
            "provider_specialty": "Internal Medicine",
            "appointment_datetime": (datetime.utcnow() + timedelta(days=i)).isoformat(),
            "appointment_type": ["new_patient", "follow_up", "procedure"][i % 3],
            "clinical_priority": ["red", "orange", "yellow", "green"][i % 4],
            "duration_minutes": [30, 45, 60][i % 3]
        }
        for i in range(1, 11)
    ]
    
    created_count = 0
    for appointment_data in sample_appointments:
        response = requests.post(f"{BASE_URL}/api/v1/appointments", json=appointment_data)
        if response.status_code == 200:
            created_count += 1
    
    print(f"✅ Created {created_count} sample appointments")

if __name__ == "__main__":
    try:
        test_system()
        
        # Optionally create sample data
        create_sample = input("\nCreate sample data for testing? (y/n): ").lower().strip()
        if create_sample == 'y':
            create_sample_data()
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the system. Make sure it's running on http://localhost:8000")
        print("   Run: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
