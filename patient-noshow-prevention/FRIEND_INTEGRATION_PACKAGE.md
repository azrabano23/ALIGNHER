# Integration Package for Phase 1 Developer

Hey! This is the technical integration guide for connecting your Phase 1 scheduling system with the Phase 2 no-show prevention system.

## 🎯 What You Need to Do (Minimal Changes)

### 1. Add One API Call After Creating Appointments

In your appointment creation workflow, add this single function call:

```python
# Your existing code
appointment = create_appointment_in_your_system(patient, provider, datetime, triage_data)

# ADD THIS ONE LINE:
send_to_noshow_prevention(appointment, triage_data)
```

### 2. Implementation Function

Add this function to your codebase:

```python
import requests
import logging
from datetime import datetime

NOSHOW_API_URL = "http://localhost:8000"  # Update with actual URL
NOSHOW_API_KEY = "your-api-key"  # We'll provide this

def send_to_noshow_prevention(appointment, triage_data):
    """
    Send appointment to no-show prevention system
    Call this immediately after creating an appointment
    """
    try:
        payload = {
            # Appointment basics
            "external_id": appointment.id,  # Your appointment ID
            "appointment_datetime": appointment.datetime.isoformat(),
            "appointment_type": appointment.type,  # "new_patient", "follow_up", "procedure"
            "duration_minutes": appointment.duration,
            
            # Patient info
            "patient_external_id": appointment.patient.id,
            "patient_first_name": appointment.patient.first_name,
            "patient_last_name": appointment.patient.last_name,
            "patient_phone": appointment.patient.phone,
            "patient_email": appointment.patient.email,
            "patient_date_of_birth": appointment.patient.date_of_birth.isoformat() if appointment.patient.date_of_birth else None,
            
            # Provider info
            "provider_external_id": appointment.provider.id,
            "provider_name": appointment.provider.name,
            "provider_specialty": appointment.provider.specialty,
            "provider_location": appointment.provider.location,
            
            # CRITICAL: Triage data from your system
            "chief_complaint": triage_data.chief_complaint,
            "clinical_priority": triage_data.priority_level,  # "red", "orange", "yellow", "green"
            "triage_notes": triage_data.notes
        }
        
        response = requests.post(
            f"{NOSHOW_API_URL}/api/v1/appointments",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {NOSHOW_API_KEY}"
            },
            timeout=10  # Don't block your system if our system is slow
        )
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"✅ No-show prevention activated for appointment {appointment.id}")
            return result
        else:
            logging.warning(f"⚠️ No-show API returned {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        logging.warning("⚠️ No-show prevention system timeout - continuing normally")
    except Exception as e:
        logging.error(f"❌ No-show prevention integration error: {e}")
    
    # Always return None on error - don't break your appointment creation
    return None
```

## 🔧 Configuration

### Environment Variables
Add these to your environment:

```bash
# .env file
NOSHOW_API_URL=http://localhost:8000
NOSHOW_API_KEY=your-secure-api-key-here
```

### Dependencies
Add to your requirements.txt:
```
requests>=2.25.0
```

## 📋 Data Mapping Guide

### Priority Levels (CRITICAL for accuracy)
Map your triage system to these values:

| Your System | Send to Phase 2 | Meaning |
|-------------|-----------------|---------|
| Urgent/Stat | "red" | Must be seen within 24-48 hours |
| High Priority | "orange" | Should be seen within 1-2 weeks |
| Routine | "yellow" | Can be seen within 2-4 weeks |
| Preventive | "green" | Flexible scheduling |

### Appointment Types
| Your System | Send to Phase 2 |
|-------------|-----------------|
| New Patient Visit | "new_patient" |
| Follow-up Visit | "follow_up" |
| Procedure/Surgery | "procedure" |

## 🧪 Testing

### 1. Test with Sample Data
```python
# Test function
def test_noshow_integration():
    sample_appointment = {
        'id': 'TEST_APPT_001',
        'datetime': datetime(2025, 10, 20, 14, 30),
        'type': 'follow_up',
        'duration': 30,
        'patient': {
            'id': 'TEST_PAT_001',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'email': 'john.doe@test.com'
        },
        'provider': {
            'id': 'TEST_PROV_001',
            'name': 'Dr. Smith',
            'specialty': 'Internal Medicine'
        }
    }
    
    sample_triage = {
        'chief_complaint': 'Follow-up for diabetes',
        'priority_level': 'yellow',
        'notes': 'Routine diabetes management'
    }
    
    result = send_to_noshow_prevention(sample_appointment, sample_triage)
    print(f"Test result: {result}")

# Run the test
test_noshow_integration()
```

### 2. Verify Integration
After calling the function, check:
- No errors in your logs
- Your appointment creation still works normally
- Phase 2 system receives the data

## 🚨 Error Handling

**Important:** The integration should NEVER break your appointment creation process.

```python
def create_appointment_with_noshow_integration(patient, provider, datetime, triage):
    try:
        # 1. Create appointment in YOUR system first (most important)
        appointment = create_appointment_in_your_system(patient, provider, datetime)
        
        # 2. Send to no-show prevention (secondary)
        noshow_result = send_to_noshow_prevention(appointment, triage)
        
        # 3. Optionally log the result
        if noshow_result:
            appointment.noshow_prevention_id = noshow_result.get('id')
            save_appointment(appointment)
        
        return appointment
        
    except Exception as e:
        # If anything fails, your appointment creation should still succeed
        logging.error(f"Appointment creation error: {e}")
        raise  # Only raise if YOUR system fails, not the integration
```

## 📊 What Happens Next (Automatic)

Once you send the appointment data:

1. **Risk Assessment** (< 1 second)
   - ML model calculates no-show probability
   - Assigns risk tier: Low/Medium/High

2. **Intervention Scheduling** (< 1 second)
   - Low Risk: Standard SMS reminder
   - Medium Risk: Pre-check-in + cost estimate + telehealth option
   - High Risk: Personal calls + transportation help + education

3. **Automatic Execution**
   - SMS sent 24-48 hours before appointment
   - Emails sent 2-3 days before
   - Staff calls scheduled for high-risk patients

## 🔍 Monitoring & Debugging

### Check Integration Status
```python
def check_appointment_status(appointment_id):
    """Check if appointment was processed by no-show system"""
    try:
        response = requests.get(
            f"{NOSHOW_API_URL}/api/v1/appointments/{appointment_id}",
            headers={"Authorization": f"Bearer {NOSHOW_API_KEY}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Risk Score: {data['risk_assessment']['risk_score']}")
            print(f"Risk Tier: {data['risk_assessment']['risk_tier']}")
            print(f"Interventions: {len(data['interventions'])}")
        return response.json()
    except Exception as e:
        print(f"Status check failed: {e}")
        return None
```

### Health Check
```python
def check_noshow_system_health():
    """Check if no-show prevention system is running"""
    try:
        response = requests.get(f"{NOSHOW_API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False
```

## 🚀 Deployment Checklist

- [ ] Add the integration function to your codebase
- [ ] Set environment variables
- [ ] Test with sample data
- [ ] Deploy to staging environment
- [ ] Test end-to-end workflow
- [ ] Monitor for errors
- [ ] Deploy to production
- [ ] Monitor integration success rate

## 📞 Support

If you run into issues:

1. **Check logs** - Look for error messages in your application logs
2. **Test connectivity** - Use the health check function
3. **Verify data format** - Ensure your data matches the expected format
4. **Contact us** - We'll help debug any integration issues

## 🎉 Expected Results

After integration:
- **No impact** on your existing appointment creation speed
- **Automatic no-show prevention** for all appointments
- **Reduced no-show rates** within 2-4 weeks
- **Staff alerts** for high-risk appointments
- **Analytics** on intervention effectiveness

The integration is designed to be **fire-and-forget** - once implemented, it works automatically in the background without requiring any ongoing maintenance from your team.
