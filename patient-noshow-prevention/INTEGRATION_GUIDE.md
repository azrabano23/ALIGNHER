# Phase 1 Integration Guide

## Overview
This guide shows how to integrate your friend's Phase 1 scheduling system with your Phase 2 no-show prevention system.

## Integration Options

### Option 1: Real-time API Calls (Recommended)
**Best for:** New integrations, clean separation of systems

**How it works:**
1. Phase 1 creates appointment in their system
2. Phase 1 immediately calls your API: `POST /api/v1/appointments`
3. Your system calculates risk and triggers interventions
4. Both systems operate independently

**Pros:** Simple, reliable, real-time
**Cons:** Requires Phase 1 code changes

### Option 2: Webhook Integration
**Best for:** Existing systems that already support webhooks

**How it works:**
1. Phase 1 creates appointment
2. Phase 1 sends webhook to your system
3. Your system processes webhook and creates appointment
4. Risk assessment and interventions triggered

**Pros:** Asynchronous, fault-tolerant
**Cons:** More complex error handling

### Option 3: Database Integration
**Best for:** Systems sharing the same database

**How it works:**
1. Database trigger fires when appointment inserted
2. Trigger calls your API or queues processing
3. Your system processes the appointment

**Pros:** No Phase 1 code changes needed
**Cons:** Tight coupling, database dependency

## Required Data Exchange

### From Phase 1 → Phase 2
```json
{
  "appointment_id": "APPT_12345",
  "patient_id": "PAT_67890",
  "patient": {
    "first_name": "Jane",
    "last_name": "Smith", 
    "phone": "+1234567890",
    "email": "jane@email.com",
    "date_of_birth": "1965-03-15"
  },
  "provider": {
    "id": "PROV_001",
    "name": "Dr. Johnson",
    "specialty": "Gynecology"
  },
  "appointment_datetime": "2025-10-18T14:30:00",
  "appointment_type": "new_patient",
  "triage": {
    "chief_complaint": "Postmenopausal bleeding",
    "priority_level": "red",
    "notes": "Urgent referral needed"
  }
}
```

### From Phase 2 → Phase 1 (Optional)
```json
{
  "appointment_id": "APPT_12345",
  "risk_assessment": {
    "risk_score": 0.75,
    "risk_tier": "high",
    "interventions_scheduled": 4
  },
  "next_intervention": "2025-10-15T10:00:00"
}
```

## Implementation Steps

### Step 1: Choose Integration Method
Discuss with your friend which method works best for their system.

### Step 2: Set Up Authentication
```python
# Add to your .env file
PHASE1_API_KEY=your-secure-api-key
PHASE1_WEBHOOK_SECRET=webhook-signing-secret
```

### Step 3: Test Integration
```bash
# Start your system
./start.sh

# Test the integration
python integration_examples/phase1_integration.py
```

### Step 4: Handle Error Cases
- Network failures
- Invalid data
- System downtime
- Rate limiting

### Step 5: Monitor Integration
- Track successful integrations
- Monitor error rates
- Set up alerts for failures

## API Endpoints for Phase 1

### Create Appointment
```
POST /api/v1/appointments
Content-Type: application/json
Authorization: Bearer {API_KEY}

{appointment_data}
```

### Get Appointment Status
```
GET /api/v1/appointments/{appointment_id}
Authorization: Bearer {API_KEY}
```

### Webhook Endpoint
```
POST /webhooks/phase1/appointment
Content-Type: application/json
X-Webhook-Signature: {signature}

{webhook_data}
```

## Error Handling

### Retry Logic
```python
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_noshow_api(appointment_data):
    response = requests.post(
        f"{NOSHOW_API_URL}/api/v1/appointments",
        json=appointment_data,
        timeout=30
    )
    response.raise_for_status()
    return response.json()
```

### Fallback Strategy
If your system is down, Phase 1 should:
1. Log the appointment for later processing
2. Continue normal operation
3. Retry when your system is back online

## Testing Checklist

- [ ] Appointment creation works
- [ ] Risk assessment triggers
- [ ] Interventions are scheduled
- [ ] Error handling works
- [ ] Authentication is secure
- [ ] Performance is acceptable
- [ ] Monitoring is in place

## Go-Live Plan

1. **Development Testing** - Test with sample data
2. **Staging Integration** - Connect staging systems
3. **Pilot Launch** - Start with one provider/location
4. **Gradual Rollout** - Expand to more providers
5. **Full Production** - All appointments processed

## Support & Monitoring

### Health Checks
Your friend's system should monitor:
- `GET /health` - System health
- Response times
- Error rates

### Alerts
Set up alerts for:
- Integration failures
- High error rates
- System downtime
- Performance degradation
