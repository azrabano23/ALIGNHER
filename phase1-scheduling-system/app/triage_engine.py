"""
AI-Powered Triage Engine for Phase 1 Scheduling System
Uses local LLM with RAG to assess patient symptoms and assign priority levels
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import json
import re
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import faiss
from app.models import TriageAssessment, TriageRequest, PriorityLevel

logger = logging.getLogger(__name__)

class TriageKnowledgeBase:
    """RAG system for medical triage protocols"""
    
    def __init__(self, protocols_file: str = "data/triage_protocols.csv"):
        self.protocols_file = protocols_file
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.protocols = []
        self.load_protocols()
        self.build_index()
    
    def load_protocols(self):
        """Load and parse OBGYN triage protocols"""
        try:
            # Create sample protocols based on the CSV structure we saw
            self.protocols = [
                {
                    "priority": "green",
                    "category": "Paperwork",
                    "symptoms": ["paperwork", "forms", "disability", "fmla", "school notes", "work notes"],
                    "smart_phrase": ".PAPERWORK",
                    "timeline": "3 business days",
                    "action": "Call will be returned within 3 business days",
                    "specialty": "administrative"
                },
                {
                    "priority": "yellow",
                    "category": "Medication Refills",
                    "symptoms": ["medication refill", "prescription", "refill", "medication"],
                    "smart_phrase": ".MEDREFILL",
                    "timeline": "2 business days",
                    "action": "Call will be returned within 2 business day",
                    "specialty": "general"
                },
                {
                    "priority": "yellow",
                    "category": "Results Requests",
                    "symptoms": ["test results", "lab results", "results", "report"],
                    "smart_phrase": ".RESULTS",
                    "timeline": "2 business days",
                    "action": "Call will be returned within 2 business day",
                    "specialty": "general"
                },
                {
                    "priority": "orange",
                    "category": "Patient Concern",
                    "symptoms": ["concern", "complaint", "worried", "symptoms"],
                    "smart_phrase": ".PATIENTCONCERN",
                    "timeline": "4 hours same day",
                    "action": "Calls will be returned within 4 business hours /same day",
                    "specialty": "clinical"
                },
                {
                    "priority": "orange",
                    "category": "Sick Patient",
                    "symptoms": ["sick", "illness", "not feeling well", "unwell"],
                    "smart_phrase": ".TRIAGE",
                    "timeline": "4 hours same day",
                    "action": "High Priority Nurse Call",
                    "specialty": "clinical"
                },
                {
                    "priority": "red",
                    "category": "Emergency Symptoms",
                    "symptoms": ["fever", "significant pain", "pain increase", "bleeding", "vomiting", "nausea", 
                               "abdominal pain", "acute pain", "black stools", "redness", "swelling", 
                               "foul smell", "drainage", "unable to urinate", "unable to have bowel movement"],
                    "smart_phrase": ".EMERGENCY",
                    "timeline": "immediate",
                    "action": "Calls to be warm transferred to the clinical call center",
                    "specialty": "emergency"
                },
                {
                    "priority": "red",
                    "category": "Post Procedure Complications",
                    "symptoms": ["post procedure", "complications", "after surgery", "post operative", 
                               "chest pain", "shortness of breath", "sob", "loss of consciousness", 
                               "suicidal ideations"],
                    "smart_phrase": ".EMERGENCY",
                    "timeline": "immediate",
                    "action": "Emergency call - warm transfer to clinical call center",
                    "specialty": "emergency"
                },
                {
                    "priority": "orange",
                    "category": "Procedure Questions",
                    "symptoms": ["procedure question", "surgery question", "what to expect", "preparation"],
                    "smart_phrase": ".PROCEDURECONCERN",
                    "timeline": "4 hours same day",
                    "action": "High Priority Nurse Call",
                    "specialty": "clinical"
                },
                {
                    "priority": "yellow",
                    "category": "Appointment Scheduling",
                    "symptoms": ["appointment", "schedule", "reschedule", "sooner appointment", "booking"],
                    "smart_phrase": ".ASCHEDULINGREQUESTS",
                    "timeline": "2 business days",
                    "action": "Appointment scheduling requests",
                    "specialty": "scheduling"
                },
                {
                    "priority": "yellow",
                    "category": "Preauthorization",
                    "symptoms": ["preauth", "preauthorization", "insurance approval", "authorization"],
                    "smart_phrase": ".PREAUTH",
                    "timeline": "2 business days",
                    "action": "Preauthorization requests",
                    "specialty": "administrative"
                }
            ]
            
            logger.info(f"Loaded {len(self.protocols)} triage protocols")
            
        except Exception as e:
            logger.error(f"Error loading protocols: {e}")
            # Fallback to basic protocols
            self.protocols = self._get_fallback_protocols()
    
    def _get_fallback_protocols(self):
        """Fallback protocols if file loading fails"""
        return [
            {
                "priority": "red",
                "category": "Emergency",
                "symptoms": ["chest pain", "bleeding", "severe pain", "unconscious"],
                "timeline": "immediate",
                "specialty": "emergency"
            },
            {
                "priority": "orange", 
                "category": "Urgent",
                "symptoms": ["pain", "fever", "nausea", "vomiting"],
                "timeline": "same day",
                "specialty": "clinical"
            },
            {
                "priority": "yellow",
                "category": "Routine",
                "symptoms": ["follow up", "results", "medication"],
                "timeline": "2 days",
                "specialty": "general"
            },
            {
                "priority": "green",
                "category": "Administrative",
                "symptoms": ["paperwork", "forms", "records"],
                "timeline": "3 days",
                "specialty": "administrative"
            }
        ]
    
    def build_index(self):
        """Build FAISS index for similarity search"""
        try:
            # Create embeddings for all protocol symptoms
            all_texts = []
            for protocol in self.protocols:
                # Combine category and symptoms for better matching
                text = f"{protocol['category']} {' '.join(protocol['symptoms'])}"
                all_texts.append(text)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(all_texts)
            
            # Build FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            logger.info(f"Built FAISS index with {len(all_texts)} protocols")
            
        except Exception as e:
            logger.error(f"Error building index: {e}")
            self.index = None
    
    def search_protocols(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant protocols based on symptoms"""
        if not self.index:
            logger.warning("Index not available, using fallback search")
            return self._fallback_search(query)
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            # Return matching protocols with scores
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.protocols):
                    protocol = self.protocols[idx].copy()
                    protocol['similarity_score'] = float(score)
                    results.append(protocol)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching protocols: {e}")
            return self._fallback_search(query)
    
    def _fallback_search(self, query: str) -> List[Dict]:
        """Simple keyword-based search fallback"""
        query_lower = query.lower()
        matches = []
        
        for protocol in self.protocols:
            score = 0
            for symptom in protocol['symptoms']:
                if symptom.lower() in query_lower:
                    score += 1
            
            if score > 0:
                protocol_copy = protocol.copy()
                protocol_copy['similarity_score'] = score / len(protocol['symptoms'])
                matches.append(protocol_copy)
        
        # Sort by score
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches[:3]

class TriageEngine:
    """Main triage engine that combines rule-based and AI-powered assessment"""
    
    def __init__(self):
        self.knowledge_base = TriageKnowledgeBase()
        self.red_flag_symptoms = [
            "chest pain", "shortness of breath", "severe bleeding", "unconscious",
            "suicidal", "severe pain", "unable to breathe", "heart attack",
            "stroke", "seizure", "loss of consciousness", "black stools",
            "severe abdominal pain", "unable to urinate", "severe headache"
        ]
        
        # OBGYN specific red flags
        self.obgyn_red_flags = [
            "postmenopausal bleeding", "severe pelvic pain", "ectopic pregnancy",
            "miscarriage", "heavy bleeding", "pregnancy complications",
            "severe morning sickness", "preeclampsia", "placental abruption"
        ]
        
        self.red_flag_symptoms.extend(self.obgyn_red_flags)
    
    def assess_patient(self, triage_request: TriageRequest) -> TriageAssessment:
        """Main triage assessment function"""
        
        # Create initial assessment
        assessment = TriageAssessment(
            patient_id=triage_request.patient_id,
            chief_complaint=triage_request.chief_complaint,
            symptoms=triage_request.symptoms,
            medical_history=triage_request.medical_history,
            current_medications=triage_request.current_medications,
            allergies=triage_request.allergies,
            pain_level=triage_request.pain_level,
            duration_of_symptoms=triage_request.duration_of_symptoms
        )
        
        # Step 1: Check for red flag symptoms (immediate red priority)
        red_flags = self._check_red_flags(triage_request)
        if red_flags:
            assessment.priority_level = PriorityLevel.RED
            assessment.red_flag_symptoms = red_flags
            assessment.doctor_visit_needed = True
            assessment.urgency_timeline = "IMMEDIATE - Emergency"
            assessment.recommended_specialty = "Emergency Medicine"
            assessment.triage_notes = f"RED FLAGS DETECTED: {', '.join(red_flags)}"
            return assessment
        
        # Step 2: Use AI/RAG to find matching protocols
        query = self._build_search_query(triage_request)
        matching_protocols = self.knowledge_base.search_protocols(query)
        
        if matching_protocols:
            best_match = matching_protocols[0]
            
            # Assign priority based on best matching protocol
            priority_map = {
                "red": PriorityLevel.RED,
                "orange": PriorityLevel.ORANGE, 
                "yellow": PriorityLevel.YELLOW,
                "green": PriorityLevel.GREEN
            }
            
            assessment.priority_level = priority_map.get(best_match['priority'], PriorityLevel.YELLOW)
            assessment.urgency_timeline = best_match.get('timeline', 'Within 2 business days')
            assessment.recommended_specialty = self._determine_specialty(best_match, triage_request)
            assessment.triage_notes = f"Matched protocol: {best_match['category']} (confidence: {best_match['similarity_score']:.2f})"
            
        else:
            # Fallback assessment
            assessment = self._fallback_assessment(assessment, triage_request)
        
        # Step 3: Apply additional rules and adjustments
        assessment = self._apply_clinical_rules(assessment, triage_request)
        
        # Step 4: Determine if doctor visit is needed
        assessment.doctor_visit_needed = self._needs_doctor_visit(assessment)
        
        # Step 5: Generate recommendations
        assessment.recommended_procedure = self._recommend_procedure(assessment, triage_request)
        
        logger.info(f"Triage assessment completed: {assessment.priority_level} priority for patient {assessment.patient_id}")
        
        return assessment
    
    def _check_red_flags(self, request: TriageRequest) -> List[str]:
        """Check for red flag symptoms that require immediate attention"""
        red_flags_found = []
        
        # Combine all patient input for checking
        all_text = f"{request.chief_complaint} {' '.join(request.symptoms)}".lower()
        
        for red_flag in self.red_flag_symptoms:
            if red_flag.lower() in all_text:
                red_flags_found.append(red_flag)
        
        # Check pain level
        if request.pain_level and request.pain_level >= 8:
            red_flags_found.append(f"Severe pain (level {request.pain_level}/10)")
        
        return red_flags_found
    
    def _build_search_query(self, request: TriageRequest) -> str:
        """Build search query for RAG system"""
        query_parts = [request.chief_complaint]
        query_parts.extend(request.symptoms)
        
        # Add relevant medical history
        if request.medical_history:
            query_parts.extend(request.medical_history[:3])  # Limit to most relevant
        
        return " ".join(query_parts)
    
    def _determine_specialty(self, protocol: Dict, request: TriageRequest) -> str:
        """Determine recommended specialty based on protocol and symptoms"""
        
        # Protocol-based specialty
        protocol_specialty = protocol.get('specialty', 'general')
        
        # OBGYN-specific routing
        obgyn_keywords = [
            "pregnancy", "pregnant", "menstrual", "period", "pelvic", "vaginal",
            "cervical", "ovarian", "uterine", "gynecology", "obstetric",
            "contraception", "birth control", "pap smear", "mammogram"
        ]
        
        all_text = f"{request.chief_complaint} {' '.join(request.symptoms)}".lower()
        
        for keyword in obgyn_keywords:
            if keyword in all_text:
                return "Obstetrics and Gynecology"
        
        # Map protocol specialties to medical specialties
        specialty_map = {
            "emergency": "Emergency Medicine",
            "clinical": "Internal Medicine", 
            "administrative": "General Practice",
            "scheduling": "General Practice",
            "general": "Internal Medicine"
        }
        
        return specialty_map.get(protocol_specialty, "Internal Medicine")
    
    def _apply_clinical_rules(self, assessment: TriageAssessment, request: TriageRequest) -> TriageAssessment:
        """Apply additional clinical decision rules"""
        
        # Age-based adjustments
        # Note: We'd need patient age from demographics for this
        
        # Pregnancy-related escalation
        pregnancy_terms = ["pregnant", "pregnancy", "expecting", "prenatal"]
        all_text = f"{request.chief_complaint} {' '.join(request.symptoms)}".lower()
        
        if any(term in all_text for term in pregnancy_terms):
            # Escalate pregnancy-related concerns
            if assessment.priority_level == PriorityLevel.GREEN:
                assessment.priority_level = PriorityLevel.YELLOW
            assessment.recommended_specialty = "Obstetrics and Gynecology"
        
        # Pain level adjustments
        if request.pain_level:
            if request.pain_level >= 7 and assessment.priority_level in [PriorityLevel.GREEN, PriorityLevel.YELLOW]:
                assessment.priority_level = PriorityLevel.ORANGE
                assessment.triage_notes += f" | Escalated due to high pain level ({request.pain_level}/10)"
        
        # Duration-based adjustments
        if request.duration_of_symptoms:
            duration_lower = request.duration_of_symptoms.lower()
            if any(term in duration_lower for term in ["weeks", "months", "chronic"]):
                # Chronic symptoms can often wait
                if assessment.priority_level == PriorityLevel.ORANGE:
                    assessment.priority_level = PriorityLevel.YELLOW
            elif any(term in duration_lower for term in ["sudden", "acute", "today", "hours"]):
                # Acute symptoms need faster attention
                if assessment.priority_level == PriorityLevel.GREEN:
                    assessment.priority_level = PriorityLevel.YELLOW
        
        return assessment
    
    def _fallback_assessment(self, assessment: TriageAssessment, request: TriageRequest) -> TriageAssessment:
        """Fallback assessment when no protocols match"""
        
        # Default to yellow (routine) priority
        assessment.priority_level = PriorityLevel.YELLOW
        assessment.urgency_timeline = "Within 2 business days"
        assessment.recommended_specialty = "Internal Medicine"
        assessment.triage_notes = "No specific protocol matched - using default assessment"
        
        # Check for common urgent keywords
        urgent_keywords = ["pain", "bleeding", "fever", "nausea", "vomiting", "dizzy"]
        all_text = f"{request.chief_complaint} {' '.join(request.symptoms)}".lower()
        
        if any(keyword in all_text for keyword in urgent_keywords):
            assessment.priority_level = PriorityLevel.ORANGE
            assessment.urgency_timeline = "Same day"
            assessment.triage_notes = "Escalated due to urgent symptoms"
        
        return assessment
    
    def _needs_doctor_visit(self, assessment: TriageAssessment) -> bool:
        """Determine if patient needs to see a doctor"""
        
        # Red and Orange always need doctor visit
        if assessment.priority_level in [PriorityLevel.RED, PriorityLevel.ORANGE]:
            return True
        
        # Yellow usually needs doctor visit unless administrative
        if assessment.priority_level == PriorityLevel.YELLOW:
            admin_keywords = ["paperwork", "forms", "records", "insurance"]
            if not any(keyword in assessment.triage_notes.lower() for keyword in admin_keywords):
                return True
        
        # Green (administrative) may not need doctor visit
        return False
    
    def _recommend_procedure(self, assessment: TriageAssessment, request: TriageRequest) -> str:
        """Recommend appropriate procedure or next steps"""
        
        if assessment.priority_level == PriorityLevel.RED:
            return "Emergency evaluation and treatment"
        elif assessment.priority_level == PriorityLevel.ORANGE:
            return "Urgent medical consultation and examination"
        elif assessment.priority_level == PriorityLevel.YELLOW:
            return "Routine medical consultation and examination"
        else:
            return "Administrative assistance or routine follow-up"

# Global triage engine instance
triage_engine = TriageEngine()
