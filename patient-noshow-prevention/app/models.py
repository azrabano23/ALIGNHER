from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class PriorityLevel(enum.Enum):
    RED = "red"
    ORANGE = "orange" 
    YELLOW = "yellow"
    GREEN = "green"

class RiskTier(enum.Enum):
    LOW = "low"      # <20% no-show risk
    MEDIUM = "medium"  # 20-60% no-show risk
    HIGH = "high"    # >60% no-show risk

class InterventionStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AppointmentOutcome(enum.Enum):
    ATTENDED = "attended"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from Phase 1 system
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    date_of_birth = Column(DateTime)
    insurance_provider = Column(String)
    preferred_language = Column(String, default="en")
    
    # Historical patterns
    total_appointments = Column(Integer, default=0)
    no_show_count = Column(Integer, default=0)
    cancellation_count = Column(Integer, default=0)
    last_appointment_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    appointments = relationship("Appointment", back_populates="patient")
    risk_profiles = relationship("PatientRiskProfile", back_populates="patient")

class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String)
    location = Column(String)
    
    # Provider-specific no-show patterns
    average_no_show_rate = Column(Float, default=0.0)
    
    appointments = relationship("Appointment", back_populates="provider")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from Phase 1 system
    
    patient_id = Column(Integer, ForeignKey("patients.id"))
    provider_id = Column(Integer, ForeignKey("providers.id"))
    
    appointment_datetime = Column(DateTime, nullable=False)
    appointment_type = Column(String)  # "new_patient", "follow_up", "procedure"
    duration_minutes = Column(Integer, default=30)
    
    # From Phase 1 triage
    chief_complaint = Column(Text)
    clinical_priority = Column(Enum(PriorityLevel))
    triage_notes = Column(Text)
    
    # Risk assessment
    no_show_risk_score = Column(Float)
    risk_tier = Column(Enum(RiskTier))
    risk_factors = Column(Text)  # JSON string of contributing factors
    
    # Outcome
    outcome = Column(Enum(AppointmentOutcome))
    attended_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("Provider", back_populates="appointments")
    interventions = relationship("Intervention", back_populates="appointment")

class PatientRiskProfile(Base):
    __tablename__ = "patient_risk_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    
    # Behavioral patterns
    preferred_appointment_time = Column(String)  # "morning", "afternoon", "evening"
    preferred_day_of_week = Column(String)
    average_lead_time_days = Column(Float)
    
    # Communication preferences
    prefers_sms = Column(Boolean, default=True)
    prefers_email = Column(Boolean, default=True)
    prefers_voice = Column(Boolean, default=False)
    
    # Risk factors
    transportation_issues = Column(Boolean, default=False)
    financial_concerns = Column(Boolean, default=False)
    anxiety_about_procedures = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="risk_profiles")

class Intervention(Base):
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    
    intervention_type = Column(String)  # "sms_reminder", "email_reminder", "pre_checkin", "human_call"
    status = Column(Enum(InterventionStatus))
    scheduled_at = Column(DateTime)
    executed_at = Column(DateTime)
    
    # Content and targeting
    message_content = Column(Text)
    target_channel = Column(String)  # "sms", "email", "voice"
    
    # Results
    delivered = Column(Boolean, default=False)
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    responded = Column(Boolean, default=False)
    
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    appointment = relationship("Appointment", back_populates="interventions")

class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False)
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    
    # Training info
    training_samples = Column(Integer)
    training_date = Column(DateTime, default=datetime.utcnow)
    feature_importance = Column(Text)  # JSON string
    
    is_active = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
