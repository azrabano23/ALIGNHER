from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class PriorityLevel(str, Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"

class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AppointmentCreate(BaseModel):
    external_id: str
    patient_external_id: str
    patient_first_name: str
    patient_last_name: str
    patient_phone: Optional[str] = None
    patient_email: Optional[EmailStr] = None
    patient_date_of_birth: Optional[datetime] = None
    provider_external_id: str
    provider_name: str
    provider_specialty: Optional[str] = None
    provider_location: Optional[str] = None
    appointment_datetime: datetime
    appointment_type: str
    duration_minutes: int = 30
    chief_complaint: Optional[str] = None
    clinical_priority: PriorityLevel = PriorityLevel.GREEN
    triage_notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    external_id: str
    patient_name: str
    provider_name: str
    appointment_datetime: datetime
    risk_score: Optional[float] = None
    risk_tier: Optional[RiskTier] = None
    status: str

    class Config:
        from_attributes = True

class RiskAssessmentRequest(BaseModel):
    appointment_id: int

class RiskFactor(BaseModel):
    factor: str
    value: Any
    importance: float

class RiskAssessmentResponse(BaseModel):
    appointment_id: int
    risk_score: float
    risk_tier: RiskTier
    confidence: float
    risk_factors: List[RiskFactor]

class InterventionTriggerRequest(BaseModel):
    appointment_id: int
    force_retrigger: bool = False

class InterventionResponse(BaseModel):
    id: int
    appointment_id: int
    intervention_type: str
    status: str
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    delivered: bool = False
    target_channel: str

    class Config:
        from_attributes = True

class PatientUpdate(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_language: Optional[str] = None
    transportation_issues: Optional[bool] = None
    financial_concerns: Optional[bool] = None
    anxiety_about_procedures: Optional[bool] = None

class AppointmentOutcomeUpdate(BaseModel):
    appointment_id: int
    outcome: str  # "attended", "no_show", "cancelled", "rescheduled"
    attended_at: Optional[datetime] = None
    notes: Optional[str] = None

class AnalyticsDashboard(BaseModel):
    total_appointments: int
    high_risk_appointments: int
    medium_risk_appointments: int
    low_risk_appointments: int
    total_interventions: int
    delivered_interventions: int
    delivery_rate: float
    no_show_rate_overall: float
    no_show_rate_by_tier: Dict[str, float]
    intervention_effectiveness: Dict[str, float]

class ModelTrainingRequest(BaseModel):
    min_samples: int = 1000
    retrain_if_exists: bool = False

class ModelPerformanceResponse(BaseModel):
    model_version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    training_samples: int
    training_date: datetime
    feature_importance: Dict[str, float]
    is_active: bool

class CommunicationPreferences(BaseModel):
    prefers_sms: bool = True
    prefers_email: bool = True
    prefers_voice: bool = False
    preferred_time: Optional[str] = None  # "morning", "afternoon", "evening"
    language: str = "en"

class WebhookEvent(BaseModel):
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]

# Phase 1 Integration Schemas
class Phase1AppointmentWebhook(BaseModel):
    """Webhook payload from Phase 1 scheduling system"""
    event_type: str  # "appointment_created", "appointment_updated", "appointment_cancelled"
    appointment_id: str
    patient_id: str
    provider_id: str
    appointment_data: AppointmentCreate
    timestamp: datetime

class Phase1PatientUpdate(BaseModel):
    """Patient update from Phase 1 system"""
    patient_id: str
    updates: PatientUpdate
    timestamp: datetime
