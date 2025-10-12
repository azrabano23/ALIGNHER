"""
Intelligent Scheduling Engine for Phase 1 System
Handles provider matching, availability checking, and appointment booking
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import logging
from app.models import (
    DoctorProfile, PatientProfile, Appointment, TriageAssessment,
    ProviderMatch, ProviderMatchRequest, AppointmentRequest,
    PriorityLevel, AppointmentStatus
)
from app.storage import storage

logger = logging.getLogger(__name__)

class ProviderMatcher:
    """Matches patients with appropriate providers based on multiple criteria"""
    
    def __init__(self):
        self.specialty_mapping = {
            "Obstetrics and Gynecology": ["obgyn", "gynecology", "obstetrics", "women's health"],
            "Internal Medicine": ["internal medicine", "general medicine", "primary care"],
            "Emergency Medicine": ["emergency", "urgent care", "emergency medicine"],
            "General Practice": ["general practice", "family medicine", "primary care"],
            "Cardiology": ["cardiology", "heart", "cardiac"],
            "Dermatology": ["dermatology", "skin", "dermatological"],
            "Gastroenterology": ["gastroenterology", "gi", "digestive", "gastro"]
        }
    
    def find_matching_providers(self, request: ProviderMatchRequest) -> List[ProviderMatch]:
        """Find providers that match patient requirements"""
        
        # Get all doctors
        all_doctors = storage.get_all_doctors()
        
        # Filter by specialty
        specialty_matches = self._filter_by_specialty(all_doctors, request.specialty)
        
        # Filter by insurance
        insurance_matches = self._filter_by_insurance(specialty_matches, request.insurance_provider)
        
        # Calculate match scores and availability
        provider_matches = []
        for doctor in insurance_matches:
            match_score = self._calculate_match_score(doctor, request)
            available_slots = self._get_available_slots(doctor, request.preferred_datetime)
            
            if available_slots:  # Only include if has availability
                provider_match = ProviderMatch(
                    doctor_id=doctor.id,
                    doctor_name=doctor.full_name,
                    specialty=doctor.specialty,
                    location=doctor.location or "Main Campus",
                    accepts_insurance=True,  # Already filtered
                    available_slots=available_slots,
                    match_score=match_score,
                    next_available=available_slots[0] if available_slots else None
                )
                provider_matches.append(provider_match)
        
        # Sort by match score (highest first)
        provider_matches.sort(key=lambda x: x.match_score, reverse=True)
        
        logger.info(f"Found {len(provider_matches)} matching providers for specialty: {request.specialty}")
        return provider_matches
    
    def _filter_by_specialty(self, doctors: List[DoctorProfile], required_specialty: str) -> List[DoctorProfile]:
        """Filter doctors by specialty with fuzzy matching"""
        matching_doctors = []
        
        for doctor in doctors:
            if self._specialty_matches(doctor.specialty, required_specialty):
                matching_doctors.append(doctor)
        
        return matching_doctors
    
    def _specialty_matches(self, doctor_specialty: str, required_specialty: str) -> bool:
        """Check if doctor specialty matches required specialty"""
        doctor_specialty_lower = doctor_specialty.lower()
        required_specialty_lower = required_specialty.lower()
        
        # Exact match
        if doctor_specialty_lower == required_specialty_lower:
            return True
        
        # Check specialty mappings
        for standard_specialty, variations in self.specialty_mapping.items():
            if required_specialty_lower in [v.lower() for v in variations]:
                if doctor_specialty_lower in [v.lower() for v in variations]:
                    return True
                if doctor_specialty_lower == standard_specialty.lower():
                    return True
        
        # Partial match
        if required_specialty_lower in doctor_specialty_lower or doctor_specialty_lower in required_specialty_lower:
            return True
        
        return False
    
    def _filter_by_insurance(self, doctors: List[DoctorProfile], insurance_provider: str) -> List[DoctorProfile]:
        """Filter doctors by accepted insurance"""
        matching_doctors = []
        
        for doctor in doctors:
            if insurance_provider in doctor.accepted_insurances:
                matching_doctors.append(doctor)
        
        return matching_doctors
    
    def _calculate_match_score(self, doctor: DoctorProfile, request: ProviderMatchRequest) -> float:
        """Calculate match score for doctor-patient pairing"""
        score = 0.0
        
        # Base score for specialty match
        if self._specialty_matches(doctor.specialty, request.specialty):
            score += 0.4
        
        # Insurance acceptance
        if request.insurance_provider in doctor.accepted_insurances:
            score += 0.3
        
        # Location preference (if specified)
        if request.preferred_location:
            if doctor.location and request.preferred_location.lower() in doctor.location.lower():
                score += 0.2
        else:
            score += 0.1  # Small bonus for having location info
        
        # Availability bonus (more available slots = higher score)
        available_slots = self._get_available_slots(doctor, request.preferred_datetime)
        if len(available_slots) > 5:
            score += 0.1
        elif len(available_slots) > 0:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_available_slots(self, doctor: DoctorProfile, preferred_datetime: Optional[datetime] = None) -> List[datetime]:
        """Get available appointment slots for a doctor"""
        
        # Get doctor's existing appointments
        existing_appointments = storage.get_appointments_by_doctor(doctor.id)
        
        # Generate potential slots (simplified - in real system would use calendar integration)
        available_slots = []
        
        # Start from tomorrow or preferred date
        start_date = preferred_datetime.date() if preferred_datetime else (datetime.now() + timedelta(days=1)).date()
        
        # Generate slots for next 30 days
        for day_offset in range(30):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends (simplified)
            if current_date.weekday() >= 5:
                continue
            
            # Generate hourly slots from 9 AM to 5 PM
            for hour in range(9, 17):
                slot_datetime = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                
                # Check if slot is already booked
                if not self._is_slot_booked(slot_datetime, existing_appointments):
                    available_slots.append(slot_datetime)
                
                # Limit to reasonable number of slots
                if len(available_slots) >= 20:
                    break
            
            if len(available_slots) >= 20:
                break
        
        return available_slots
    
    def _is_slot_booked(self, slot_datetime: datetime, appointments: List[Appointment]) -> bool:
        """Check if a time slot is already booked"""
        for appointment in appointments:
            # Check if appointment overlaps with slot (assuming 30-60 min appointments)
            appointment_end = appointment.appointment_datetime + timedelta(minutes=appointment.duration_minutes)
            slot_end = slot_datetime + timedelta(minutes=30)  # Assume 30 min default
            
            if (slot_datetime < appointment_end and slot_end > appointment.appointment_datetime):
                return True
        
        return False

class SchedulingEngine:
    """Main scheduling engine that coordinates provider matching and appointment booking"""
    
    def __init__(self):
        self.provider_matcher = ProviderMatcher()
        self.priority_weights = {
            PriorityLevel.RED: 1.0,      # Immediate
            PriorityLevel.ORANGE: 0.8,   # Same day
            PriorityLevel.YELLOW: 0.6,   # 2 days
            PriorityLevel.GREEN: 0.4     # 3 days
        }
    
    def schedule_appointment(self, request: AppointmentRequest) -> Tuple[Optional[Appointment], str]:
        """Main appointment scheduling function"""
        
        try:
            # Get patient and triage information
            patient = storage.get_patient_by_id(request.patient_id)
            if not patient:
                return None, "Patient not found"
            
            triage = storage.get_triage_by_id(request.triage_id)
            if not triage:
                return None, "Triage assessment not found"
            
            # Create provider match request
            provider_request = ProviderMatchRequest(
                specialty=triage.recommended_specialty,
                insurance_provider=request.insurance_provider,
                preferred_datetime=request.preferred_datetime,
                telehealth_ok=request.telehealth_preferred
            )
            
            # Find matching providers
            matching_providers = self.provider_matcher.find_matching_providers(provider_request)
            
            if not matching_providers:
                return None, f"No providers found for specialty: {triage.recommended_specialty}"
            
            # Select best provider and time slot
            selected_provider, selected_datetime = self._select_optimal_slot(
                matching_providers, triage, request
            )
            
            if not selected_provider or not selected_datetime:
                return None, "No available appointment slots found"
            
            # Get doctor profile
            doctor = storage.get_doctor_by_id(selected_provider.doctor_id)
            if not doctor:
                return None, "Selected doctor not found"
            
            # Create appointment
            appointment = Appointment(
                patient_id=request.patient_id,
                doctor_id=selected_provider.doctor_id,
                triage_id=request.triage_id,
                appointment_datetime=selected_datetime,
                duration_minutes=self._calculate_appointment_duration(triage),
                appointment_type=self._determine_appointment_type(triage),
                chief_complaint=triage.chief_complaint,
                priority_level=triage.priority_level,
                recommended_specialty=triage.recommended_specialty,
                location=selected_provider.location,
                telehealth=request.telehealth_preferred,
                scheduling_notes=request.special_requirements
            )
            
            # Save appointment
            created_appointment = storage.create_appointment(appointment)
            
            logger.info(f"Scheduled appointment {created_appointment.id} for patient {request.patient_id}")
            
            return created_appointment, "Appointment scheduled successfully"
            
        except Exception as e:
            logger.error(f"Error scheduling appointment: {e}")
            return None, f"Scheduling error: {str(e)}"
    
    def _select_optimal_slot(self, providers: List[ProviderMatch], triage: TriageAssessment, 
                           request: AppointmentRequest) -> Tuple[Optional[ProviderMatch], Optional[datetime]]:
        """Select optimal provider and time slot based on priority and preferences"""
        
        # Get priority weight
        priority_weight = self.priority_weights.get(triage.priority_level, 0.5)
        
        best_provider = None
        best_datetime = None
        best_score = 0.0
        
        for provider in providers:
            for slot_datetime in provider.available_slots:
                
                # Calculate slot score
                slot_score = self._calculate_slot_score(
                    provider, slot_datetime, triage, request, priority_weight
                )
                
                if slot_score > best_score:
                    best_score = slot_score
                    best_provider = provider
                    best_datetime = slot_datetime
        
        return best_provider, best_datetime
    
    def _calculate_slot_score(self, provider: ProviderMatch, slot_datetime: datetime,
                            triage: TriageAssessment, request: AppointmentRequest,
                            priority_weight: float) -> float:
        """Calculate score for a specific provider-slot combination"""
        
        score = 0.0
        
        # Provider match score (40% of total)
        score += provider.match_score * 0.4
        
        # Timing score based on priority (40% of total)
        timing_score = self._calculate_timing_score(slot_datetime, triage.priority_level, request.preferred_datetime)
        score += timing_score * 0.4 * priority_weight
        
        # Preference bonus (20% of total)
        if request.preferred_datetime:
            time_diff = abs((slot_datetime - request.preferred_datetime).total_seconds())
            # Closer to preferred time = higher score
            preference_score = max(0, 1 - (time_diff / (24 * 3600)))  # Normalize by 24 hours
            score += preference_score * 0.2
        
        return score
    
    def _calculate_timing_score(self, slot_datetime: datetime, priority: PriorityLevel, 
                              preferred_datetime: Optional[datetime]) -> float:
        """Calculate timing score based on priority requirements"""
        
        now = datetime.now()
        hours_until_slot = (slot_datetime - now).total_seconds() / 3600
        
        # Priority-based timing requirements
        if priority == PriorityLevel.RED:
            # Red: Immediate (within 4 hours is ideal)
            if hours_until_slot <= 4:
                return 1.0
            elif hours_until_slot <= 24:
                return 0.7
            else:
                return 0.3
        
        elif priority == PriorityLevel.ORANGE:
            # Orange: Same day (within 24 hours)
            if hours_until_slot <= 24:
                return 1.0
            elif hours_until_slot <= 48:
                return 0.8
            else:
                return 0.5
        
        elif priority == PriorityLevel.YELLOW:
            # Yellow: Within 2 business days
            if hours_until_slot <= 48:
                return 1.0
            elif hours_until_slot <= 72:
                return 0.9
            else:
                return 0.7
        
        else:  # GREEN
            # Green: Within 3 business days
            if hours_until_slot <= 72:
                return 1.0
            else:
                return 0.8
    
    def _calculate_appointment_duration(self, triage: TriageAssessment) -> int:
        """Calculate appointment duration based on triage assessment"""
        
        # Base duration by priority
        base_durations = {
            PriorityLevel.RED: 60,      # Emergency - longer time needed
            PriorityLevel.ORANGE: 45,   # Urgent - thorough examination
            PriorityLevel.YELLOW: 30,   # Routine - standard time
            PriorityLevel.GREEN: 15     # Administrative - quick
        }
        
        base_duration = base_durations.get(triage.priority_level, 30)
        
        # Adjust for procedure type
        if triage.recommended_procedure:
            procedure_lower = triage.recommended_procedure.lower()
            if any(word in procedure_lower for word in ["surgery", "procedure", "biopsy"]):
                base_duration += 30
            elif any(word in procedure_lower for word in ["consultation", "examination"]):
                base_duration += 15
        
        return base_duration
    
    def _determine_appointment_type(self, triage: TriageAssessment) -> str:
        """Determine appointment type based on triage"""
        
        if triage.priority_level == PriorityLevel.RED:
            return "emergency_consultation"
        elif triage.priority_level == PriorityLevel.ORANGE:
            return "urgent_consultation"
        elif "follow" in triage.chief_complaint.lower():
            return "follow_up"
        elif any(word in triage.chief_complaint.lower() for word in ["procedure", "surgery", "biopsy"]):
            return "procedure"
        else:
            return "consultation"
    
    def reschedule_appointment(self, appointment_id: str, new_datetime: datetime) -> Tuple[bool, str]:
        """Reschedule an existing appointment"""
        
        try:
            appointment = storage.get_appointment_by_id(appointment_id)
            if not appointment:
                return False, "Appointment not found"
            
            # Check if new time slot is available
            doctor = storage.get_doctor_by_id(appointment.doctor_id)
            if not doctor:
                return False, "Doctor not found"
            
            available_slots = self.provider_matcher._get_available_slots(doctor, new_datetime)
            
            # Check if requested time is available (within 30 minutes)
            slot_available = any(
                abs((slot - new_datetime).total_seconds()) <= 1800  # 30 minutes
                for slot in available_slots
            )
            
            if not slot_available:
                return False, "Requested time slot is not available"
            
            # Update appointment
            appointment.appointment_datetime = new_datetime
            appointment.updated_at = datetime.utcnow()
            
            storage.update_appointment(appointment)
            
            logger.info(f"Rescheduled appointment {appointment_id} to {new_datetime}")
            return True, "Appointment rescheduled successfully"
            
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {e}")
            return False, f"Rescheduling error: {str(e)}"
    
    def cancel_appointment(self, appointment_id: str, reason: str = "") -> Tuple[bool, str]:
        """Cancel an existing appointment"""
        
        try:
            appointment = storage.get_appointment_by_id(appointment_id)
            if not appointment:
                return False, "Appointment not found"
            
            appointment.status = AppointmentStatus.CANCELLED
            appointment.scheduling_notes = f"Cancelled: {reason}" if reason else "Cancelled"
            appointment.updated_at = datetime.utcnow()
            
            storage.update_appointment(appointment)
            
            logger.info(f"Cancelled appointment {appointment_id}")
            return True, "Appointment cancelled successfully"
            
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return False, f"Cancellation error: {str(e)}"

# Global scheduling engine instance
scheduling_engine = SchedulingEngine()
