"""
Phase 1: Smart Triage & Intelligent Scheduling System
Main FastAPI application
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import httpx

from app.models import (
    User, UserCreate, DoctorProfile, DoctorRegister, PatientProfile, PatientRegister,
    TriageAssessment, TriageRequest, Appointment, AppointmentRequest,
    ProviderMatchRequest, ProviderMatch, PriorityLevel, UserRole,
    TriageResponse, AppointmentResponse, DoctorResponse, PatientResponse
)
from app.storage import storage
from app.triage_engine import triage_engine
from app.scheduling_engine import scheduling_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Phase 1: Smart Triage & Scheduling System",
    description="AI-powered triage and intelligent appointment scheduling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for integrated frontend
app.mount("/static", StaticFiles(directory="integrated_frontend"), name="static")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Phase 2 Integration Configuration
PHASE2_API_URL = "http://localhost:8000"  # No-show prevention system URL

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

@app.get("/")
async def root():
    return FileResponse("integrated_frontend/index.html")

@app.get("/api")
async def api_info():
    return {
        "message": "Phase 1: Smart Triage & Scheduling System",
        "status": "running",
        "features": [
            "AI-powered triage assessment",
            "Intelligent provider matching",
            "Automated appointment scheduling",
            "Phase 2 integration for no-show prevention"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Doctor Registration and Management
@app.post("/api/v1/doctors/register", response_model=DoctorResponse)
async def register_doctor(doctor_data: DoctorRegister):
    """Register a new doctor"""
    try:
        # Create user account
        user = User(
            email=doctor_data.email,
            password_hash=hash_password(doctor_data.password),
            role=UserRole.DOCTOR
        )
        
        created_user = storage.create_user(user)
        
        # Create doctor profile
        doctor_profile = DoctorProfile(
            user_id=created_user.id,
            full_name=doctor_data.full_name,
            specialty=doctor_data.specialty,
            credentials=doctor_data.credentials,
            accepted_insurances=doctor_data.accepted_insurances,
            hospital_affiliation=doctor_data.hospital_affiliation,
            phone=doctor_data.phone,
            location=doctor_data.location
        )
        
        created_doctor = storage.create_doctor(doctor_profile)
        
        logger.info(f"Registered new doctor: {created_doctor.full_name}")
        
        return DoctorResponse(
            doctor_id=created_doctor.id,
            full_name=created_doctor.full_name,
            specialty=created_doctor.specialty,
            credentials=created_doctor.credentials,
            location=created_doctor.location or "Main Campus",
            phone=created_doctor.phone
        )
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Doctor registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/api/v1/doctors", response_model=List[DoctorResponse])
async def get_doctors(specialty: Optional[str] = None):
    """Get all doctors, optionally filtered by specialty"""
    try:
        if specialty:
            doctors = storage.get_doctors_by_specialty(specialty)
        else:
            doctors = storage.get_all_doctors()
        
        return [
            DoctorResponse(
                doctor_id=doctor.id,
                full_name=doctor.full_name,
                specialty=doctor.specialty,
                credentials=doctor.credentials,
                location=doctor.location or "Main Campus",
                phone=doctor.phone
            )
            for doctor in doctors
        ]
        
    except Exception as e:
        logger.error(f"Error fetching doctors: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch doctors")

# Patient Registration and Management
@app.post("/api/v1/patients/register", response_model=PatientResponse)
async def register_patient(patient_data: PatientRegister):
    """Register a new patient"""
    try:
        # Create user account
        user = User(
            email=patient_data.email,
            password_hash=hash_password(patient_data.password),
            role=UserRole.PATIENT
        )
        
        created_user = storage.create_user(user)
        
        # Create patient profile
        patient_profile = PatientProfile(
            user_id=created_user.id,
            demographics=patient_data.demographics,
            insurance=patient_data.insurance,
            telehealth_preference=patient_data.telehealth_preference,
            consents=patient_data.consents,
            medical_history=patient_data.medical_history,
            allergies=patient_data.allergies
        )
        
        created_patient = storage.create_patient(patient_profile)
        
        logger.info(f"Registered new patient: {created_patient.demographics.first_name} {created_patient.demographics.last_name}")
        
        return PatientResponse(
            patient_id=created_patient.id,
            full_name=f"{created_patient.demographics.first_name} {created_patient.demographics.last_name}",
            phone=created_patient.demographics.phone,
            email=created_user.email,
            insurance_provider=created_patient.insurance.provider
        )
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Patient registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

# Triage System
@app.post("/api/v1/triage/assess", response_model=TriageResponse)
async def assess_patient_triage(triage_request: TriageRequest):
    """Perform AI-powered triage assessment"""
    try:
        # Validate patient exists
        patient = storage.get_patient_by_id(triage_request.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Perform triage assessment
        assessment = triage_engine.assess_patient(triage_request)
        
        # Save assessment
        saved_assessment = storage.create_triage_assessment(assessment)
        
        logger.info(f"Triage assessment completed: {saved_assessment.priority_level} for patient {triage_request.patient_id}")
        
        # Generate next steps based on priority
        next_steps = _generate_next_steps(saved_assessment)
        
        return TriageResponse(
            triage_id=saved_assessment.id,
            priority_level=saved_assessment.priority_level,
            recommended_specialty=saved_assessment.recommended_specialty,
            recommended_procedure=saved_assessment.recommended_procedure or "Medical consultation",
            doctor_visit_needed=saved_assessment.doctor_visit_needed,
            urgency_timeline=saved_assessment.urgency_timeline or "Within 2 business days",
            red_flag_symptoms=saved_assessment.red_flag_symptoms or [],
            next_steps=next_steps,
            estimated_appointment_duration=_estimate_duration(saved_assessment)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Triage assessment error: {e}")
        raise HTTPException(status_code=500, detail="Triage assessment failed")

def _generate_next_steps(assessment: TriageAssessment) -> str:
    """Generate next steps based on triage assessment"""
    if assessment.priority_level == PriorityLevel.RED:
        return "URGENT: Seek immediate medical attention. Call 911 or go to emergency room if symptoms worsen."
    elif assessment.priority_level == PriorityLevel.ORANGE:
        return "Schedule appointment today. Contact your healthcare provider immediately."
    elif assessment.priority_level == PriorityLevel.YELLOW:
        return "Schedule appointment within 2 business days. Monitor symptoms."
    else:
        return "Contact office for administrative assistance or routine follow-up."

def _estimate_duration(assessment: TriageAssessment) -> int:
    """Estimate appointment duration based on assessment"""
    duration_map = {
        PriorityLevel.RED: 60,
        PriorityLevel.ORANGE: 45,
        PriorityLevel.YELLOW: 30,
        PriorityLevel.GREEN: 15
    }
    return duration_map.get(assessment.priority_level, 30)

# Provider Matching
@app.post("/api/v1/providers/match", response_model=List[ProviderMatch])
async def find_matching_providers(match_request: ProviderMatchRequest):
    """Find providers matching patient requirements"""
    try:
        matches = scheduling_engine.provider_matcher.find_matching_providers(match_request)
        
        logger.info(f"Found {len(matches)} provider matches for specialty: {match_request.specialty}")
        
        return matches
        
    except Exception as e:
        logger.error(f"Provider matching error: {e}")
        raise HTTPException(status_code=500, detail="Provider matching failed")

# Appointment Scheduling
@app.post("/api/v1/appointments/schedule", response_model=AppointmentResponse)
async def schedule_appointment(
    appointment_request: AppointmentRequest,
    background_tasks: BackgroundTasks
):
    """Schedule a new appointment"""
    try:
        # Schedule appointment
        appointment, message = scheduling_engine.schedule_appointment(appointment_request)
        
        if not appointment:
            raise HTTPException(status_code=400, detail=message)
        
        # Get patient and doctor info for response
        patient = storage.get_patient_by_id(appointment.patient_id)
        doctor = storage.get_doctor_by_id(appointment.doctor_id)
        
        if not patient or not doctor:
            raise HTTPException(status_code=500, detail="Failed to retrieve appointment details")
        
        # Trigger Phase 2 integration in background
        background_tasks.add_task(
            integrate_with_phase2,
            appointment,
            patient,
            doctor
        )
        
        logger.info(f"Scheduled appointment {appointment.id}")
        
        return AppointmentResponse(
            appointment_id=appointment.id,
            patient_name=f"{patient.demographics.first_name} {patient.demographics.last_name}",
            doctor_name=doctor.full_name,
            appointment_datetime=appointment.appointment_datetime,
            location=appointment.location or "Main Campus",
            priority_level=appointment.priority_level,
            confirmation_number=f"CONF-{appointment.id[-8:].upper()}",
            telehealth=appointment.telehealth,
            preparation_instructions=_generate_preparation_instructions(appointment)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Appointment scheduling error: {e}")
        raise HTTPException(status_code=500, detail="Appointment scheduling failed")

def _generate_preparation_instructions(appointment: Appointment) -> str:
    """Generate preparation instructions based on appointment"""
    instructions = ["Arrive 15 minutes early for check-in"]
    
    if appointment.priority_level in [PriorityLevel.RED, PriorityLevel.ORANGE]:
        instructions.append("Bring a list of current medications and symptoms")
    
    if appointment.telehealth:
        instructions.append("Ensure you have a stable internet connection and quiet space")
    else:
        instructions.append("Bring your insurance card and photo ID")
    
    return ". ".join(instructions) + "."

# Appointment Management
@app.get("/api/v1/appointments/{appointment_id}")
async def get_appointment(appointment_id: str):
    """Get appointment details"""
    try:
        appointment = storage.get_appointment_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        patient = storage.get_patient_by_id(appointment.patient_id)
        doctor = storage.get_doctor_by_id(appointment.doctor_id)
        triage = storage.get_triage_by_id(appointment.triage_id) if appointment.triage_id else None
        
        return {
            "appointment": appointment,
            "patient": patient,
            "doctor": doctor,
            "triage": triage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching appointment: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointment")

@app.put("/api/v1/appointments/{appointment_id}/reschedule")
async def reschedule_appointment(appointment_id: str, new_datetime: datetime):
    """Reschedule an existing appointment"""
    try:
        success, message = scheduling_engine.reschedule_appointment(appointment_id, new_datetime)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {"message": message, "new_datetime": new_datetime}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rescheduling error: {e}")
        raise HTTPException(status_code=500, detail="Rescheduling failed")

@app.delete("/api/v1/appointments/{appointment_id}")
async def cancel_appointment(appointment_id: str, reason: str = ""):
    """Cancel an existing appointment"""
    try:
        success, message = scheduling_engine.cancel_appointment(appointment_id, reason)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {"message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancellation error: {e}")
        raise HTTPException(status_code=500, detail="Cancellation failed")

# Analytics and Reporting
@app.get("/api/v1/analytics/dashboard")
async def get_analytics_dashboard():
    """Get system analytics and metrics"""
    try:
        all_appointments = storage.get_all_appointments()
        all_doctors = storage.get_all_doctors()
        all_patients = storage.get_all_patients()
        
        # Calculate metrics
        total_appointments = len(all_appointments)
        
        priority_counts = {}
        for priority in PriorityLevel:
            priority_counts[priority.value] = len([
                a for a in all_appointments if a.priority_level == priority
            ])
        
        specialty_counts = {}
        for doctor in all_doctors:
            specialty = doctor.specialty
            specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1
        
        return {
            "total_appointments": total_appointments,
            "total_doctors": len(all_doctors),
            "total_patients": len(all_patients),
            "priority_distribution": priority_counts,
            "specialty_distribution": specialty_counts,
            "system_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Analytics unavailable")

# Phase 2 Integration
async def integrate_with_phase2(appointment: Appointment, patient: PatientProfile, doctor: DoctorProfile):
    """Integrate with Phase 2 no-show prevention system"""
    try:
        # Get triage data
        triage = storage.get_triage_by_id(appointment.triage_id) if appointment.triage_id else None
        
        # Prepare data for Phase 2
        phase2_data = {
            "external_id": appointment.id,
            "patient_external_id": patient.id,
            "patient_first_name": patient.demographics.first_name,
            "patient_last_name": patient.demographics.last_name,
            "patient_phone": patient.demographics.phone,
            "patient_email": storage.get_user_by_id(patient.user_id).email,
            "patient_date_of_birth": patient.demographics.date_of_birth,
            
            "provider_external_id": doctor.id,
            "provider_name": doctor.full_name,
            "provider_specialty": doctor.specialty,
            "provider_location": doctor.location,
            
            "appointment_datetime": appointment.appointment_datetime.isoformat(),
            "appointment_type": appointment.appointment_type,
            "duration_minutes": appointment.duration_minutes,
            
            "chief_complaint": appointment.chief_complaint,
            "clinical_priority": appointment.priority_level.value,
            "triage_notes": triage.triage_notes if triage else ""
        }
        
        # Call Phase 2 API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PHASE2_API_URL}/api/v1/appointments",
                json=phase2_data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Update appointment to mark Phase 2 integration
                appointment.noshow_prevention_triggered = True
                result = response.json()
                appointment.noshow_risk_score = result.get('risk_score')
                storage.update_appointment(appointment)
                
                logger.info(f"Successfully integrated appointment {appointment.id} with Phase 2")
            else:
                logger.warning(f"Phase 2 integration failed: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"Phase 2 integration error: {e}")
        # Don't fail the appointment creation if Phase 2 integration fails

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
