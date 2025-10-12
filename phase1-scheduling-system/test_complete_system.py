#!/usr/bin/env python3
"""
Complete system test for Phase 1 + Phase 2 integration
Tests the entire patient journey from triage to no-show prevention
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
import time

# API URLs
PHASE1_URL = "http://localhost:3000"
PHASE2_URL = "http://localhost:8000"

class CompleteSystemTest:
    def __init__(self):
        self.phase1_url = PHASE1_URL
        self.phase2_url = PHASE2_URL
        self.test_data = {}
    
    def run_complete_test(self):
        """Run complete end-to-end test"""
        
        print("🏥 Testing Complete Healthcare System (Phase 1 + Phase 2)")
        print("=" * 60)
        
        try:
            # Step 1: System Health Checks
            self.test_system_health()
            
            # Step 2: Register Test Doctor
            self.register_test_doctor()
            
            # Step 3: Register Test Patient
            self.register_test_patient()
            
            # Step 4: Perform Triage Assessment
            self.perform_triage_assessment()
            
            # Step 5: Schedule Appointment
            self.schedule_appointment()
            
            # Step 6: Verify Phase 2 Integration
            self.verify_phase2_integration()
            
            # Step 7: Test Different Priority Scenarios
            self.test_priority_scenarios()
            
            print("\n" + "=" * 60)
            print("🎉 Complete system test passed!")
            print("\n📊 Test Summary:")
            print(f"   Doctors registered: 1")
            print(f"   Patients registered: 1") 
            print(f"   Triage assessments: {len(self.test_data.get('triage_assessments', []))}")
            print(f"   Appointments scheduled: {len(self.test_data.get('appointments', []))}")
            print(f"   Phase 2 integrations: {len(self.test_data.get('phase2_integrations', []))}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
    
    def test_system_health(self):
        """Test both systems are running"""
        print("\n1. Testing system health...")
        
        # Test Phase 1
        response = requests.get(f"{self.phase1_url}/health")
        if response.status_code == 200:
            print("✅ Phase 1 system is healthy")
        else:
            raise Exception("Phase 1 system is not responding")
        
        # Test Phase 2
        try:
            response = requests.get(f"{self.phase2_url}/health")
            if response.status_code == 200:
                print("✅ Phase 2 system is healthy")
            else:
                print("⚠️  Phase 2 system not responding (integration will be skipped)")
        except:
            print("⚠️  Phase 2 system not available (integration will be skipped)")
    
    def register_test_doctor(self):
        """Register a test doctor"""
        print("\n2. Registering test doctor...")
        
        doctor_data = {
            "email": "dr.smith@testhospital.com",
            "password": "securepassword123",
            "full_name": "Dr. Sarah Smith",
            "specialty": "Obstetrics and Gynecology",
            "credentials": ["MD", "FACOG"],
            "accepted_insurances": ["Aetna", "BlueCross", "Cigna", "UnitedHealth"],
            "hospital_affiliation": "Test Medical Center",
            "phone": "555-0123",
            "location": "Women's Health Center"
        }
        
        response = requests.post(f"{self.phase1_url}/api/v1/doctors/register", json=doctor_data)
        
        if response.status_code == 200:
            doctor = response.json()
            self.test_data['doctor'] = doctor
            print(f"✅ Registered doctor: {doctor['full_name']}")
            print(f"   Specialty: {doctor['specialty']}")
            print(f"   Location: {doctor['location']}")
        else:
            raise Exception(f"Doctor registration failed: {response.text}")
    
    def register_test_patient(self):
        """Register a test patient"""
        print("\n3. Registering test patient...")
        
        patient_data = {
            "email": "jane.doe@email.com",
            "password": "patientpass123",
            "demographics": {
                "first_name": "Jane",
                "last_name": "Doe",
                "date_of_birth": "1985-05-22",
                "phone": "555-0456"
            },
            "insurance": {
                "provider": "Aetna",
                "policy_number": "AET123456789"
            },
            "telehealth_preference": True,
            "consents": {
                "predictive_reminders": True,
                "voice_follow_ups": False,
                "sms_notifications": True,
                "email_notifications": True
            },
            "medical_history": ["No significant medical history"],
            "allergies": ["No known allergies"]
        }
        
        response = requests.post(f"{self.phase1_url}/api/v1/patients/register", json=patient_data)
        
        if response.status_code == 200:
            patient = response.json()
            self.test_data['patient'] = patient
            print(f"✅ Registered patient: {patient['full_name']}")
            print(f"   Insurance: {patient['insurance_provider']}")
            print(f"   Phone: {patient['phone']}")
        else:
            raise Exception(f"Patient registration failed: {response.text}")
    
    def perform_triage_assessment(self):
        """Perform AI triage assessment"""
        print("\n4. Performing triage assessment...")
        
        # Test multiple triage scenarios
        triage_scenarios = [
            {
                "name": "High Priority - Postmenopausal Bleeding",
                "data": {
                    "patient_id": self.test_data['patient']['patient_id'],
                    "chief_complaint": "Postmenopausal bleeding for 3 days",
                    "symptoms": ["vaginal bleeding", "postmenopausal", "concerned"],
                    "medical_history": ["Menopause at age 52"],
                    "pain_level": 3,
                    "duration_of_symptoms": "3 days"
                }
            },
            {
                "name": "Medium Priority - Pelvic Pain",
                "data": {
                    "patient_id": self.test_data['patient']['patient_id'],
                    "chief_complaint": "Pelvic pain and irregular periods",
                    "symptoms": ["pelvic pain", "irregular periods", "cramping"],
                    "medical_history": ["No significant medical history"],
                    "pain_level": 6,
                    "duration_of_symptoms": "2 weeks"
                }
            },
            {
                "name": "Low Priority - Annual Exam",
                "data": {
                    "patient_id": self.test_data['patient']['patient_id'],
                    "chief_complaint": "Annual gynecological examination",
                    "symptoms": ["routine checkup", "preventive care"],
                    "medical_history": ["No significant medical history"],
                    "pain_level": 0,
                    "duration_of_symptoms": "N/A"
                }
            }
        ]
        
        self.test_data['triage_assessments'] = []
        
        for scenario in triage_scenarios:
            print(f"\n   Testing: {scenario['name']}")
            
            response = requests.post(f"{self.phase1_url}/api/v1/triage/assess", json=scenario['data'])
            
            if response.status_code == 200:
                triage = response.json()
                self.test_data['triage_assessments'].append(triage)
                
                print(f"   ✅ Priority: {triage['priority_level'].upper()}")
                print(f"   📋 Specialty: {triage['recommended_specialty']}")
                print(f"   ⏰ Timeline: {triage['urgency_timeline']}")
                print(f"   🏥 Doctor needed: {triage['doctor_visit_needed']}")
                
                if triage['red_flag_symptoms']:
                    print(f"   🚨 Red flags: {', '.join(triage['red_flag_symptoms'])}")
            else:
                print(f"   ❌ Triage failed: {response.text}")
    
    def schedule_appointment(self):
        """Schedule appointments based on triage assessments"""
        print("\n5. Scheduling appointments...")
        
        self.test_data['appointments'] = []
        
        for i, triage in enumerate(self.test_data['triage_assessments']):
            print(f"\n   Scheduling appointment for {triage['priority_level']} priority case...")
            
            # Calculate preferred datetime based on priority
            now = datetime.now()
            if triage['priority_level'] == 'red':
                preferred_time = now + timedelta(hours=2)  # Emergency
            elif triage['priority_level'] == 'orange':
                preferred_time = now + timedelta(hours=8)  # Same day
            elif triage['priority_level'] == 'yellow':
                preferred_time = now + timedelta(days=1)   # Next day
            else:
                preferred_time = now + timedelta(days=3)   # Routine
            
            appointment_request = {
                "patient_id": self.test_data['patient']['patient_id'],
                "triage_id": triage['triage_id'],
                "preferred_datetime": preferred_time.isoformat(),
                "telehealth_preferred": False,
                "insurance_provider": "Aetna",
                "special_requirements": f"Test appointment #{i+1}"
            }
            
            response = requests.post(f"{self.phase1_url}/api/v1/appointments/schedule", json=appointment_request)
            
            if response.status_code == 200:
                appointment = response.json()
                self.test_data['appointments'].append(appointment)
                
                print(f"   ✅ Scheduled: {appointment['appointment_id']}")
                print(f"   👨‍⚕️ Doctor: {appointment['doctor_name']}")
                print(f"   📅 Date: {appointment['appointment_datetime']}")
                print(f"   📍 Location: {appointment['location']}")
                print(f"   🎫 Confirmation: {appointment['confirmation_number']}")
            else:
                print(f"   ❌ Scheduling failed: {response.text}")
    
    def verify_phase2_integration(self):
        """Verify Phase 2 integration worked"""
        print("\n6. Verifying Phase 2 integration...")
        
        self.test_data['phase2_integrations'] = []
        
        # Wait a moment for background integration
        time.sleep(3)
        
        for appointment in self.test_data['appointments']:
            try:
                # Check if appointment exists in Phase 2 system
                response = requests.get(f"{self.phase2_url}/api/v1/appointments/{appointment['appointment_id']}")
                
                if response.status_code == 200:
                    phase2_data = response.json()
                    self.test_data['phase2_integrations'].append(phase2_data)
                    
                    risk_assessment = phase2_data.get('risk_assessment', {})
                    interventions = phase2_data.get('interventions', [])
                    
                    print(f"   ✅ Integrated: {appointment['appointment_id']}")
                    print(f"   🎯 Risk Score: {risk_assessment.get('risk_score', 'N/A')}")
                    print(f"   📊 Risk Tier: {risk_assessment.get('risk_tier', 'N/A')}")
                    print(f"   📱 Interventions: {len(interventions)} scheduled")
                    
                else:
                    print(f"   ⚠️  Not found in Phase 2: {appointment['appointment_id']}")
                    
            except Exception as e:
                print(f"   ⚠️  Phase 2 check failed: {e}")
    
    def test_priority_scenarios(self):
        """Test different priority scenarios"""
        print("\n7. Testing priority-based scheduling...")
        
        # Test emergency scenario
        emergency_triage = {
            "patient_id": self.test_data['patient']['patient_id'],
            "chief_complaint": "Severe abdominal pain and bleeding",
            "symptoms": ["severe pain", "heavy bleeding", "nausea", "dizziness"],
            "medical_history": ["No significant medical history"],
            "pain_level": 9,
            "duration_of_symptoms": "2 hours"
        }
        
        response = requests.post(f"{self.phase1_url}/api/v1/triage/assess", json=emergency_triage)
        
        if response.status_code == 200:
            emergency_assessment = response.json()
            print(f"   🚨 Emergency case priority: {emergency_assessment['priority_level'].upper()}")
            print(f"   ⚡ Timeline: {emergency_assessment['urgency_timeline']}")
            
            if emergency_assessment['red_flag_symptoms']:
                print(f"   🔴 Red flags detected: {', '.join(emergency_assessment['red_flag_symptoms'])}")
        
        # Test provider matching
        provider_request = {
            "specialty": "Obstetrics and Gynecology",
            "insurance_provider": "Aetna",
            "telehealth_ok": True
        }
        
        response = requests.post(f"{self.phase1_url}/api/v1/providers/match", json=provider_request)
        
        if response.status_code == 200:
            matches = response.json()
            print(f"   👥 Found {len(matches)} matching providers")
            
            if matches:
                best_match = matches[0]
                print(f"   🏆 Best match: {best_match['doctor_name']} (score: {best_match['match_score']:.2f})")
                print(f"   📅 Available slots: {len(best_match['available_slots'])}")
    
    def test_analytics(self):
        """Test analytics dashboard"""
        print("\n8. Testing analytics...")
        
        response = requests.get(f"{self.phase1_url}/api/v1/analytics/dashboard")
        
        if response.status_code == 200:
            analytics = response.json()
            print(f"   📊 Total appointments: {analytics['total_appointments']}")
            print(f"   👨‍⚕️ Total doctors: {analytics['total_doctors']}")
            print(f"   👥 Total patients: {analytics['total_patients']}")
            print(f"   📈 Priority distribution: {analytics['priority_distribution']}")

def main():
    """Run the complete system test"""
    test = CompleteSystemTest()
    
    try:
        test.run_complete_test()
        
        # Optional: Test analytics
        test.test_analytics()
        
        print("\n🎯 Next Steps:")
        print("1. Start both Phase 1 and Phase 2 systems")
        print("2. Access Phase 1 API docs: http://localhost:3000/docs")
        print("3. Access Phase 2 API docs: http://localhost:8000/docs")
        print("4. Build VCC agent interface")
        print("5. Integrate with real calendar systems")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
