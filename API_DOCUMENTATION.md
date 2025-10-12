# 📡 API Documentation

## 🏥 **Complete Healthcare System APIs**

This document provides comprehensive API documentation for both Phase 1 (Triage & Scheduling) and Phase 2 (No-Show Prevention) systems.

---

## 🩺 **Phase 1: Smart Triage & Scheduling API**

**Base URL**: `http://localhost:3000/api/v1`

### **Authentication**
Currently using development mode. Production will implement JWT tokens.

### **Core Endpoints**

#### **🏥 System Health**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-10-12T10:30:00.000Z"
}
```

---

#### **👨‍⚕️ Doctor Management**

##### **Register Doctor**
```http
POST /doctors/register
```

**Request Body:**
```json
{
  "email": "dr.smith@hospital.com",
  "password": "securepassword123",
  "full_name": "Dr. Sarah Smith",
  "specialty": "Obstetrics and Gynecology",
  "credentials": ["MD", "FACOG"],
  "accepted_insurances": ["Aetna", "BlueCross", "Cigna"],
  "hospital_affiliation": "Main Medical Center",
  "phone": "555-0123",
  "location": "Women's Health Center"
}
```

**Response:**
```json
{
  "doctor_id": "doctor-12345-abcde",
  "full_name": "Dr. Sarah Smith",
  "specialty": "Obstetrics and Gynecology",
  "credentials": ["MD", "FACOG"],
  "location": "Women's Health Center",
  "phone": "555-0123"
}
```

##### **Get Doctors**
```http
GET /doctors?specialty=Obstetrics and Gynecology
```

**Response:**
```json
[
  {
    "doctor_id": "doctor-12345-abcde",
    "full_name": "Dr. Sarah Smith",
    "specialty": "Obstetrics and Gynecology",
    "credentials": ["MD", "FACOG"],
    "location": "Women's Health Center",
    "phone": "555-0123"
  }
]
```

---

#### **👥 Patient Management**

##### **Register Patient**
```http
POST /patients/register
```

**Request Body:**
```json
{
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
  "telehealth_preference": true,
  "consents": {
    "predictive_reminders": true,
    "voice_follow_ups": false,
    "sms_notifications": true,
    "email_notifications": true
  },
  "medical_history": ["No significant medical history"],
  "allergies": ["No known allergies"]
}
```

**Response:**
```json
{
  "patient_id": "patient-67890-fghij",
  "full_name": "Jane Doe",
  "phone": "555-0456",
  "email": "jane.doe@email.com",
  "insurance_provider": "Aetna"
}
```

---

#### **🩺 Triage Assessment**

##### **Perform AI Triage**
```http
POST /triage/assess
```

**Request Body:**
```json
{
  "patient_id": "patient-67890-fghij",
  "chief_complaint": "Pelvic pain and irregular periods",
  "symptoms": ["pelvic pain", "irregular periods", "cramping"],
  "medical_history": ["No significant medical history"],
  "current_medications": [],
  "allergies": ["No known allergies"],
  "pain_level": 6,
  "duration_of_symptoms": "2 weeks"
}
```

**Response:**
```json
{
  "triage_id": "triage-11111-kkkkk",
  "priority_level": "orange",
  "recommended_specialty": "Obstetrics and Gynecology",
  "recommended_procedure": "Urgent medical consultation and examination",
  "doctor_visit_needed": true,
  "urgency_timeline": "Same day",
  "red_flag_symptoms": [],
  "next_steps": "Schedule appointment today. Contact your healthcare provider immediately.",
  "estimated_appointment_duration": 45
}
```

**Priority Levels:**
- `red`: Emergency (immediate attention)
- `orange`: Urgent (same day)
- `yellow`: Routine (within 2 days)
- `green`: Administrative (within 3 days)

---

#### **👥 Provider Matching**

##### **Find Matching Providers**
```http
POST /providers/match
```

**Request Body:**
```json
{
  "specialty": "Obstetrics and Gynecology",
  "insurance_provider": "Aetna",
  "preferred_location": "Main Campus",
  "preferred_datetime": "2024-10-15T10:00:00Z",
  "telehealth_ok": true
}
```

**Response:**
```json
[
  {
    "doctor_id": "doctor-12345-abcde",
    "doctor_name": "Dr. Sarah Smith",
    "specialty": "Obstetrics and Gynecology",
    "location": "Women's Health Center",
    "accepts_insurance": true,
    "available_slots": [
      "2024-10-15T10:00:00Z",
      "2024-10-15T11:00:00Z",
      "2024-10-15T14:00:00Z"
    ],
    "match_score": 0.95,
    "next_available": "2024-10-15T10:00:00Z"
  }
]
```

---

#### **📅 Appointment Scheduling**

##### **Schedule Appointment**
```http
POST /appointments/schedule
```

**Request Body:**
```json
{
  "patient_id": "patient-67890-fghij",
  "triage_id": "triage-11111-kkkkk",
  "preferred_datetime": "2024-10-15T10:00:00Z",
  "preferred_doctor_id": "doctor-12345-abcde",
  "telehealth_preferred": false,
  "insurance_provider": "Aetna",
  "special_requirements": "Wheelchair accessible"
}
```

**Response:**
```json
{
  "appointment_id": "appt-22222-lllll",
  "patient_name": "Jane Doe",
  "doctor_name": "Dr. Sarah Smith",
  "appointment_datetime": "2024-10-15T10:00:00Z",
  "location": "Women's Health Center",
  "priority_level": "orange",
  "confirmation_number": "CONF-22222LLL",
  "telehealth": false,
  "preparation_instructions": "Arrive 15 minutes early for check-in. Bring your insurance card and photo ID."
}
```

##### **Get Appointment**
```http
GET /appointments/{appointment_id}
```

**Response:**
```json
{
  "appointment": {
    "id": "appt-22222-lllll",
    "patient_id": "patient-67890-fghij",
    "doctor_id": "doctor-12345-abcde",
    "appointment_datetime": "2024-10-15T10:00:00Z",
    "status": "scheduled",
    "priority_level": "orange"
  },
  "patient": {
    "demographics": {
      "first_name": "Jane",
      "last_name": "Doe",
      "phone": "555-0456"
    }
  },
  "doctor": {
    "full_name": "Dr. Sarah Smith",
    "specialty": "Obstetrics and Gynecology"
  },
  "triage": {
    "priority_level": "orange",
    "chief_complaint": "Pelvic pain and irregular periods"
  }
}
```

##### **Reschedule Appointment**
```http
PUT /appointments/{appointment_id}/reschedule
```

**Request Body:**
```json
{
  "new_datetime": "2024-10-16T14:00:00Z"
}
```

##### **Cancel Appointment**
```http
DELETE /appointments/{appointment_id}
```

**Request Body:**
```json
{
  "reason": "Patient requested cancellation"
}
```

---

#### **📊 Analytics**

##### **Get System Analytics**
```http
GET /analytics/dashboard
```

**Response:**
```json
{
  "total_appointments": 150,
  "total_doctors": 12,
  "total_patients": 89,
  "priority_distribution": {
    "red": 5,
    "orange": 25,
    "yellow": 95,
    "green": 25
  },
  "specialty_distribution": {
    "Obstetrics and Gynecology": 8,
    "Internal Medicine": 4
  },
  "system_status": "operational"
}
```

---

## 🎯 **Phase 2: No-Show Prevention API**

**Base URL**: `http://localhost:8000/api/v1`

### **Core Endpoints**

#### **🏥 System Health**
```http
GET /health
```

#### **📅 Appointment Management**

##### **Create Appointment (from Phase 1)**
```http
POST /appointments
```

**Request Body:**
```json
{
  "external_id": "appt-22222-lllll",
  "patient_external_id": "patient-67890-fghij",
  "patient_first_name": "Jane",
  "patient_last_name": "Doe",
  "patient_phone": "555-0456",
  "patient_email": "jane.doe@email.com",
  "patient_date_of_birth": "1985-05-22",
  "provider_external_id": "doctor-12345-abcde",
  "provider_name": "Dr. Sarah Smith",
  "provider_specialty": "Obstetrics and Gynecology",
  "appointment_datetime": "2024-10-15T10:00:00Z",
  "appointment_type": "consultation",
  "duration_minutes": 45,
  "chief_complaint": "Pelvic pain and irregular periods",
  "clinical_priority": "orange",
  "triage_notes": "Urgent consultation needed"
}
```

**Response:**
```json
{
  "appointment_id": "ns-appt-33333-mmmmm",
  "external_id": "appt-22222-lllll",
  "risk_assessment": {
    "risk_score": 0.35,
    "risk_tier": "Medium",
    "factors": {
      "patient_history": 0.2,
      "appointment_details": 0.4,
      "clinical_context": 0.3
    }
  },
  "interventions_scheduled": 3,
  "next_intervention": "2024-10-14T09:00:00Z"
}
```

##### **Get Appointment with Risk Data**
```http
GET /appointments/{appointment_id}
```

**Response:**
```json
{
  "appointment": {
    "id": "ns-appt-33333-mmmmm",
    "external_id": "appt-22222-lllll",
    "appointment_datetime": "2024-10-15T10:00:00Z",
    "status": "scheduled"
  },
  "risk_assessment": {
    "risk_score": 0.35,
    "risk_tier": "Medium",
    "last_updated": "2024-10-12T10:30:00Z"
  },
  "interventions": [
    {
      "intervention_type": "sms_reminder",
      "scheduled_time": "2024-10-14T09:00:00Z",
      "status": "scheduled"
    },
    {
      "intervention_type": "pre_checkin",
      "scheduled_time": "2024-10-15T08:00:00Z",
      "status": "scheduled"
    }
  ]
}
```

---

#### **📱 Intervention Management**

##### **Trigger Interventions**
```http
POST /interventions/trigger
```

**Request Body:**
```json
{
  "appointment_id": "ns-appt-33333-mmmmm"
}
```

**Response:**
```json
{
  "interventions_triggered": 2,
  "campaign_type": "medium_risk",
  "next_intervention_time": "2024-10-14T09:00:00Z",
  "estimated_effectiveness": 0.75
}
```

##### **Get Intervention History**
```http
GET /interventions/history/{appointment_id}
```

**Response:**
```json
[
  {
    "intervention_id": "int-44444-nnnnn",
    "intervention_type": "sms_reminder",
    "sent_at": "2024-10-14T09:00:00Z",
    "status": "delivered",
    "response_received": false
  },
  {
    "intervention_id": "int-55555-ooooo",
    "intervention_type": "email_reminder",
    "sent_at": "2024-10-14T18:00:00Z",
    "status": "opened",
    "response_received": true
  }
]
```

---

#### **📊 Analytics & Performance**

##### **Get No-Show Analytics**
```http
GET /analytics/dashboard
```

**Response:**
```json
{
  "total_appointments": 500,
  "no_show_rate": 0.12,
  "baseline_no_show_rate": 0.25,
  "improvement": 0.52,
  "cost_savings": 125000,
  "interventions_sent": 1250,
  "intervention_effectiveness": {
    "sms_reminder": 0.65,
    "email_reminder": 0.45,
    "voice_call": 0.85,
    "pre_checkin": 0.75
  },
  "risk_distribution": {
    "Low": 300,
    "Medium": 150,
    "High": 50
  }
}
```

---

## 🔧 **Error Handling**

### **Standard Error Response**
```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-10-12T10:30:00Z"
}
```

### **Common HTTP Status Codes**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `409`: Conflict (e.g., duplicate email)
- `422`: Validation Error
- `500`: Internal Server Error

### **Validation Errors**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🔗 **Integration Examples**

### **Complete Patient Journey**
```javascript
// 1. Register Patient
const patient = await registerPatient(patientData);

// 2. Perform Triage
const triage = await performTriage({
  patient_id: patient.patient_id,
  chief_complaint: "Pelvic pain",
  symptoms: ["pain", "irregular periods"]
});

// 3. Find Providers
const providers = await findProviders({
  specialty: triage.recommended_specialty,
  insurance_provider: "Aetna"
});

// 4. Schedule Appointment
const appointment = await scheduleAppointment({
  patient_id: patient.patient_id,
  triage_id: triage.triage_id,
  preferred_doctor_id: providers[0].doctor_id
});

// 5. Automatic Phase 2 Integration (happens automatically)
// Risk assessment and interventions are triggered in background
```

---

## 📞 **Support & Testing**

### **Interactive API Documentation**
- **Phase 1**: http://localhost:3000/docs
- **Phase 2**: http://localhost:8000/docs

### **Test Endpoints**
Use the simple test interface: http://localhost:3000/static/simple.html

### **Postman Collection**
Import the API endpoints into Postman for testing:
```json
{
  "info": {
    "name": "Healthcare System APIs",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Phase 1 - Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:3000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "3000",
          "path": ["health"]
        }
      }
    }
  ]
}
```

---

**🎉 Complete API documentation for the integrated healthcare system!** 🏥✨
