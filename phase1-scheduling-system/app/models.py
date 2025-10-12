"""
Data models for Phase 1 Scheduling System
Using text file storage as specified in requirements
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import json

class UserRole(str, Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"
    VCC_AGENT = "vcc_agent"

class PriorityLevel(str, Enum):
    GREEN = "green"      # Low priority - 3 business days
    YELLOW = "yellow"    # Routine - 2 business days  
    ORANGE = "orange"    # High priority - 4 hours/same day
    RED = "red"          # Urgent - warm transfer to clinical call center

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

# User Account Models
class User(BaseModel):
    id: str = None
    email: EmailStr
    password_hash: str
    role: UserRole
    created_at: datetime = None
    
    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = f"user-{uuid.uuid4()}"
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole

# Doctor Models
class DoctorProfile(BaseModel):
    id: str = None
    user_id: str
    full_name: str
    specialty: str
    credentials: List[str]
    accepted_insurances: List[str]
    hospital_affiliation: str
    phone: Optional[str] = None
    location: Optional[str] = None
    availability_schedule: Optional[Dict[str, Any]] = {}  # Store calendar data
    created_at: datetime = None
    
    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = f"doctor-{uuid.uuid4()}"
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)

class DoctorRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    specialty: str
    credentials: List[str]
    accepted_insurances: List[str]
    hospital_affiliation: str
    phone: Optional[str] = None
    location: Optional[str] = None

# Patient Models
class PatientDemographics(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # YYYY-MM-DD format
    phone: str

class PatientInsurance(BaseModel):
    provider: str
    policy_number: str

class PatientConsents(BaseModel):
    predictive_reminders: bool = True
    voice_follow_ups: bool = False
    sms_notifications: bool = True
    email_notifications: bool = True

class PatientProfile(BaseModel):
    id: str = None
    user_id: str
    demographics: PatientDemographics
    insurance: PatientInsurance
    telehealth_preference: bool = False
    consents: PatientConsents
    medical_history: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    emergency_contact: Optional[Dict[str, str]] = {}
    created_at: datetime = None
    
    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = f"patient-{uuid.uuid4()}"
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)

class PatientRegister(BaseModel):
    email: EmailStr
    password: str
    demographics: PatientDemographics
    insurance: PatientInsurance
    telehealth_preference: bool = False
    consents: PatientConsents
    medical_history: Optional[List[str]] = []
    allergies: Optional[List[str]] = []

# Triage Models
class TriageAssessment(BaseModel):
    id: str = None
    patient_id: str
    vcc_agent_id: Optional[str] = None
    chief_complaint: str
    symptoms: List[str]
    medical_history: List[str]
    current_medications: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    pain_level: Optional[int] = None  # 1-10 scale
    duration_of_symptoms: Optional[str] = None
    
    # AI Assessment Results
    priority_level: Optional[PriorityLevel] = None
    recommended_specialty: Optional[str] = None
    recommended_procedure: Optional[str] = None
    doctor_visit_needed: Optional[bool] = None
    urgency_timeline: Optional[str] = None
    triage_notes: Optional[str] = None
    red_flag_symptoms: Optional[List[str]] = []
    
    created_at: datetime = None
    
    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = f"triage-{uuid.uuid4()}"
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)

class TriageRequest(BaseModel):
    patient_id: str
    chief_complaint: str
    symptoms: List[str]
    medical_history: List[str] = []
    current_medications: List[str] = []
    allergies: List[str] = []
    pain_level: Optional[int] = None
    duration_of_symptoms: Optional[str] = None

# Appointment Models
class Appointment(BaseModel):
    id: str = None
    patient_id: str
    doctor_id: str
    triage_id: Optional[str] = None
    
    appointment_datetime: datetime
    duration_minutes: int = 30
    appointment_type: str  # "consultation", "follow_up", "procedure"
    
    # From triage
    chief_complaint: str
    priority_level: PriorityLevel
    recommended_specialty: str
    
    # Scheduling details
    location: Optional[str] = None
    room_number: Optional[str] = None
    telehealth: bool = False
    
    # Status tracking
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    confirmation_sent: bool = False
    reminder_sent: bool = False
    
    # Integration with Phase 2
    noshow_prevention_triggered: bool = False
    noshow_risk_score: Optional[float] = None
    
    # Notes
    scheduling_notes: Optional[str] = None
    clinical_notes: Optional[str] = None
    
    created_at: datetime = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = f"appt-{uuid.uuid4()}"
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        if data.get('updated_at') is None:
            data['updated_at'] = datetime.utcnow()
        super().__init__(**data)

class AppointmentRequest(BaseModel):
    patient_id: str
    triage_id: str
    preferred_datetime: Optional[datetime] = None
    preferred_doctor_id: Optional[str] = None
    telehealth_preferred: bool = False
    insurance_provider: str
    special_requirements: Optional[str] = None

# Provider Matching Models
class ProviderMatch(BaseModel):
    doctor_id: str
    doctor_name: str
    specialty: str
    location: str
    accepts_insurance: bool
    available_slots: List[datetime]
    match_score: float  # 0.0 to 1.0
    distance_miles: Optional[float] = None
    next_available: datetime

class ProviderMatchRequest(BaseModel):
    specialty: str
    insurance_provider: str
    preferred_location: Optional[str] = None
    preferred_datetime: Optional[datetime] = None
    max_distance_miles: Optional[float] = None
    telehealth_ok: bool = False

# Calendar Integration Models
class CalendarEvent(BaseModel):
    id: str
    title: str
    start_datetime: datetime
    end_datetime: datetime
    attendees: List[str] = []
    location: Optional[str] = None
    description: Optional[str] = None

class AvailabilitySlot(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    available: bool
    appointment_id: Optional[str] = None

# Response Models
class TriageResponse(BaseModel):
    triage_id: str
    priority_level: PriorityLevel
    recommended_specialty: str
    recommended_procedure: str
    doctor_visit_needed: bool
    urgency_timeline: str
    red_flag_symptoms: List[str]
    next_steps: str
    estimated_appointment_duration: int

class AppointmentResponse(BaseModel):
    appointment_id: str
    patient_name: str
    doctor_name: str
    appointment_datetime: datetime
    location: str
    priority_level: PriorityLevel
    confirmation_number: str
    telehealth: bool
    preparation_instructions: Optional[str] = None

class DoctorResponse(BaseModel):
    doctor_id: str
    full_name: str
    specialty: str
    credentials: List[str]
    location: str
    phone: Optional[str] = None

class PatientResponse(BaseModel):
    patient_id: str
    full_name: str
    phone: str
    email: str
    insurance_provider: str
