"""
Text file storage system for Phase 1 Scheduling System
Each file stores one JSON object per line as specified
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from app.models import User, DoctorProfile, PatientProfile, Appointment, TriageAssessment

logger = logging.getLogger(__name__)

class TextFileStorage:
    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = storage_dir
        self.users_file = os.path.join(storage_dir, "users.txt")
        self.doctors_file = os.path.join(storage_dir, "doctors.txt")
        self.patients_file = os.path.join(storage_dir, "patients.txt")
        self.appointments_file = os.path.join(storage_dir, "appointments.txt")
        self.triage_file = os.path.join(storage_dir, "triage_assessments.txt")
        
        # Create storage directory and files if they don't exist
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Create storage directory and files if they don't exist"""
        os.makedirs(self.storage_dir, exist_ok=True)
        
        for file_path in [self.users_file, self.doctors_file, self.patients_file, 
                         self.appointments_file, self.triage_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass  # Create empty file
    
    def _read_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read all JSON objects from a file"""
        objects = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            obj = json.loads(line)
                            objects.append(obj)
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing JSON line in {file_path}: {e}")
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
        return objects
    
    def _write_object(self, file_path: str, obj: Dict[str, Any]):
        """Append a JSON object to a file"""
        try:
            # Convert datetime objects to ISO format strings
            obj_copy = self._serialize_datetime(obj)
            
            with open(file_path, 'a') as f:
                f.write(json.dumps(obj_copy) + '\n')
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")
            raise
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """Recursively convert datetime objects to ISO format strings"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        else:
            return obj
    
    def _deserialize_datetime(self, obj: Any) -> Any:
        """Recursively convert ISO format strings back to datetime objects"""
        if isinstance(obj, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(obj.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return obj
        elif isinstance(obj, dict):
            return {key: self._deserialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_datetime(item) for item in obj]
        else:
            return obj
    
    def _update_file(self, file_path: str, updated_objects: List[Dict[str, Any]]):
        """Rewrite entire file with updated objects"""
        try:
            with open(file_path, 'w') as f:
                for obj in updated_objects:
                    obj_copy = self._serialize_datetime(obj)
                    f.write(json.dumps(obj_copy) + '\n')
        except Exception as e:
            logger.error(f"Error updating {file_path}: {e}")
            raise
    
    # User operations
    def create_user(self, user: User) -> User:
        """Create a new user"""
        # Check if email already exists
        if self.get_user_by_email(user.email):
            raise ValueError(f"User with email {user.email} already exists")
        
        user_dict = user.dict()
        self._write_object(self.users_file, user_dict)
        logger.info(f"Created user: {user.id}")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = self._read_file(self.users_file)
        for user_data in users:
            if user_data.get('email') == email:
                user_data = self._deserialize_datetime(user_data)
                return User(**user_data)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self._read_file(self.users_file)
        for user_data in users:
            if user_data.get('id') == user_id:
                user_data = self._deserialize_datetime(user_data)
                return User(**user_data)
        return None
    
    # Doctor operations
    def create_doctor(self, doctor: DoctorProfile) -> DoctorProfile:
        """Create a new doctor profile"""
        doctor_dict = doctor.dict()
        self._write_object(self.doctors_file, doctor_dict)
        logger.info(f"Created doctor: {doctor.id}")
        return doctor
    
    def get_doctor_by_id(self, doctor_id: str) -> Optional[DoctorProfile]:
        """Get doctor by ID"""
        doctors = self._read_file(self.doctors_file)
        for doctor_data in doctors:
            if doctor_data.get('id') == doctor_id:
                doctor_data = self._deserialize_datetime(doctor_data)
                return DoctorProfile(**doctor_data)
        return None
    
    def get_doctor_by_user_id(self, user_id: str) -> Optional[DoctorProfile]:
        """Get doctor by user ID"""
        doctors = self._read_file(self.doctors_file)
        for doctor_data in doctors:
            if doctor_data.get('user_id') == user_id:
                doctor_data = self._deserialize_datetime(doctor_data)
                return DoctorProfile(**doctor_data)
        return None
    
    def get_doctors_by_specialty(self, specialty: str) -> List[DoctorProfile]:
        """Get all doctors by specialty"""
        doctors = self._read_file(self.doctors_file)
        matching_doctors = []
        for doctor_data in doctors:
            if doctor_data.get('specialty', '').lower() == specialty.lower():
                doctor_data = self._deserialize_datetime(doctor_data)
                matching_doctors.append(DoctorProfile(**doctor_data))
        return matching_doctors
    
    def get_doctors_by_insurance(self, insurance_provider: str) -> List[DoctorProfile]:
        """Get all doctors that accept specific insurance"""
        doctors = self._read_file(self.doctors_file)
        matching_doctors = []
        for doctor_data in doctors:
            accepted_insurances = doctor_data.get('accepted_insurances', [])
            if insurance_provider in accepted_insurances:
                doctor_data = self._deserialize_datetime(doctor_data)
                matching_doctors.append(DoctorProfile(**doctor_data))
        return matching_doctors
    
    # Patient operations
    def create_patient(self, patient: PatientProfile) -> PatientProfile:
        """Create a new patient profile"""
        patient_dict = patient.dict()
        self._write_object(self.patients_file, patient_dict)
        logger.info(f"Created patient: {patient.id}")
        return patient
    
    def get_patient_by_id(self, patient_id: str) -> Optional[PatientProfile]:
        """Get patient by ID"""
        patients = self._read_file(self.patients_file)
        for patient_data in patients:
            if patient_data.get('id') == patient_id:
                patient_data = self._deserialize_datetime(patient_data)
                return PatientProfile(**patient_data)
        return None
    
    def get_patient_by_user_id(self, user_id: str) -> Optional[PatientProfile]:
        """Get patient by user ID"""
        patients = self._read_file(self.patients_file)
        for patient_data in patients:
            if patient_data.get('user_id') == user_id:
                patient_data = self._deserialize_datetime(patient_data)
                return PatientProfile(**patient_data)
        return None
    
    # Triage operations
    def create_triage_assessment(self, triage: TriageAssessment) -> TriageAssessment:
        """Create a new triage assessment"""
        triage_dict = triage.dict()
        self._write_object(self.triage_file, triage_dict)
        logger.info(f"Created triage assessment: {triage.id}")
        return triage
    
    def get_triage_by_id(self, triage_id: str) -> Optional[TriageAssessment]:
        """Get triage assessment by ID"""
        triages = self._read_file(self.triage_file)
        for triage_data in triages:
            if triage_data.get('id') == triage_id:
                triage_data = self._deserialize_datetime(triage_data)
                return TriageAssessment(**triage_data)
        return None
    
    def update_triage_assessment(self, triage: TriageAssessment) -> TriageAssessment:
        """Update an existing triage assessment"""
        triages = self._read_file(self.triage_file)
        updated_triages = []
        found = False
        
        for triage_data in triages:
            if triage_data.get('id') == triage.id:
                triage_data = triage.dict()
                found = True
            updated_triages.append(triage_data)
        
        if not found:
            raise ValueError(f"Triage assessment {triage.id} not found")
        
        self._update_file(self.triage_file, updated_triages)
        logger.info(f"Updated triage assessment: {triage.id}")
        return triage
    
    # Appointment operations
    def create_appointment(self, appointment: Appointment) -> Appointment:
        """Create a new appointment"""
        appointment_dict = appointment.dict()
        self._write_object(self.appointments_file, appointment_dict)
        logger.info(f"Created appointment: {appointment.id}")
        return appointment
    
    def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID"""
        appointments = self._read_file(self.appointments_file)
        for appointment_data in appointments:
            if appointment_data.get('id') == appointment_id:
                appointment_data = self._deserialize_datetime(appointment_data)
                return Appointment(**appointment_data)
        return None
    
    def get_appointments_by_patient(self, patient_id: str) -> List[Appointment]:
        """Get all appointments for a patient"""
        appointments = self._read_file(self.appointments_file)
        patient_appointments = []
        for appointment_data in appointments:
            if appointment_data.get('patient_id') == patient_id:
                appointment_data = self._deserialize_datetime(appointment_data)
                patient_appointments.append(Appointment(**appointment_data))
        return patient_appointments
    
    def get_appointments_by_doctor(self, doctor_id: str) -> List[Appointment]:
        """Get all appointments for a doctor"""
        appointments = self._read_file(self.appointments_file)
        doctor_appointments = []
        for appointment_data in appointments:
            if appointment_data.get('doctor_id') == doctor_id:
                appointment_data = self._deserialize_datetime(appointment_data)
                doctor_appointments.append(Appointment(**appointment_data))
        return doctor_appointments
    
    def update_appointment(self, appointment: Appointment) -> Appointment:
        """Update an existing appointment"""
        appointments = self._read_file(self.appointments_file)
        updated_appointments = []
        found = False
        
        for appointment_data in appointments:
            if appointment_data.get('id') == appointment.id:
                appointment.updated_at = datetime.utcnow()
                appointment_data = appointment.dict()
                found = True
            updated_appointments.append(appointment_data)
        
        if not found:
            raise ValueError(f"Appointment {appointment.id} not found")
        
        self._update_file(self.appointments_file, updated_appointments)
        logger.info(f"Updated appointment: {appointment.id}")
        return appointment
    
    # Analytics and reporting
    def get_all_appointments(self) -> List[Appointment]:
        """Get all appointments"""
        appointments = self._read_file(self.appointments_file)
        all_appointments = []
        for appointment_data in appointments:
            appointment_data = self._deserialize_datetime(appointment_data)
            all_appointments.append(Appointment(**appointment_data))
        return all_appointments
    
    def get_all_doctors(self) -> List[DoctorProfile]:
        """Get all doctors"""
        doctors = self._read_file(self.doctors_file)
        all_doctors = []
        for doctor_data in doctors:
            doctor_data = self._deserialize_datetime(doctor_data)
            all_doctors.append(DoctorProfile(**doctor_data))
        return all_doctors
    
    def get_all_patients(self) -> List[PatientProfile]:
        """Get all patients"""
        patients = self._read_file(self.patients_file)
        all_patients = []
        for patient_data in patients:
            patient_data = self._deserialize_datetime(patient_data)
            all_patients.append(PatientProfile(**patient_data))
        return all_patients

# Global storage instance
storage = TextFileStorage()
