import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class NoShowRiskPredictor:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
    def prepare_features(self, appointment_data: Dict) -> pd.DataFrame:
        """
        Convert appointment data into ML features
        """
        features = {}
        
        # Temporal features
        appt_datetime = pd.to_datetime(appointment_data['appointment_datetime'])
        now = datetime.utcnow()
        
        features['lead_time_days'] = (appt_datetime - now).days
        features['appointment_hour'] = appt_datetime.hour
        features['appointment_day_of_week'] = appt_datetime.weekday()
        features['is_monday'] = 1 if appt_datetime.weekday() == 0 else 0
        features['is_friday'] = 1 if appt_datetime.weekday() == 4 else 0
        features['is_morning'] = 1 if appt_datetime.hour < 12 else 0
        features['is_afternoon'] = 1 if 12 <= appt_datetime.hour < 17 else 0
        
        # Patient history features
        patient = appointment_data.get('patient', {})
        features['patient_age'] = self._calculate_age(patient.get('date_of_birth'))
        features['total_appointments'] = patient.get('total_appointments', 0)
        features['no_show_count'] = patient.get('no_show_count', 0)
        features['cancellation_count'] = patient.get('cancellation_count', 0)
        
        # Calculate historical no-show rate
        total_past = features['total_appointments']
        if total_past > 0:
            features['historical_no_show_rate'] = features['no_show_count'] / total_past
        else:
            features['historical_no_show_rate'] = 0.0
            
        # Days since last appointment
        last_appt = patient.get('last_appointment_date')
        if last_appt:
            features['days_since_last_appointment'] = (now - pd.to_datetime(last_appt)).days
        else:
            features['days_since_last_appointment'] = 999  # New patient
            
        # Clinical priority (from Phase 1)
        priority_mapping = {'red': 4, 'orange': 3, 'yellow': 2, 'green': 1}
        features['clinical_priority_score'] = priority_mapping.get(
            appointment_data.get('clinical_priority', 'green').lower(), 1
        )
        
        # Appointment type features
        appt_type = appointment_data.get('appointment_type', 'follow_up').lower()
        features['is_new_patient'] = 1 if appt_type == 'new_patient' else 0
        features['is_procedure'] = 1 if appt_type == 'procedure' else 0
        features['is_follow_up'] = 1 if appt_type == 'follow_up' else 0
        
        # Duration
        features['duration_minutes'] = appointment_data.get('duration_minutes', 30)
        features['is_long_appointment'] = 1 if features['duration_minutes'] > 60 else 0
        
        # Provider features
        provider = appointment_data.get('provider', {})
        features['provider_no_show_rate'] = provider.get('average_no_show_rate', 0.15)
        
        # Specialty risk (some specialties have higher no-show rates)
        specialty = provider.get('specialty', '').lower()
        high_risk_specialties = ['psychiatry', 'pain_management', 'addiction_medicine']
        features['high_risk_specialty'] = 1 if specialty in high_risk_specialties else 0
        
        # Risk profile features
        risk_profile = appointment_data.get('risk_profile', {})
        features['transportation_issues'] = 1 if risk_profile.get('transportation_issues') else 0
        features['financial_concerns'] = 1 if risk_profile.get('financial_concerns') else 0
        features['anxiety_about_procedures'] = 1 if risk_profile.get('anxiety_about_procedures') else 0
        
        # Communication preferences
        features['prefers_sms'] = 1 if risk_profile.get('prefers_sms') else 0
        features['prefers_email'] = 1 if risk_profile.get('prefers_email') else 0
        
        # Seasonal factors
        features['is_winter'] = 1 if appt_datetime.month in [12, 1, 2] else 0
        features['is_holiday_season'] = 1 if appt_datetime.month in [11, 12] else 0
        
        return pd.DataFrame([features])
    
    def _calculate_age(self, date_of_birth) -> int:
        """Calculate age from date of birth"""
        if not date_of_birth:
            return 35  # Default age
        
        dob = pd.to_datetime(date_of_birth)
        today = datetime.utcnow()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    def train(self, training_data: List[Dict]) -> Dict:
        """
        Train the no-show prediction model
        """
        logger.info(f"Training model with {len(training_data)} samples")
        
        # Prepare features for all training samples
        feature_dfs = []
        labels = []
        
        for sample in training_data:
            features_df = self.prepare_features(sample)
            feature_dfs.append(features_df)
            
            # Label: 1 if no-show, 0 if attended
            outcome = sample.get('outcome', 'attended').lower()
            labels.append(1 if outcome == 'no_show' else 0)
        
        # Combine all features
        X = pd.concat(feature_dfs, ignore_index=True)
        y = np.array(labels)
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        # Handle categorical variables (if any)
        # For now, all features are numeric
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'auc_roc': roc_auc_score(y_test, y_pred_proba),
            'training_samples': len(training_data),
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
        }
        
        logger.info(f"Model trained. Accuracy: {metrics['accuracy']:.3f}, AUC: {metrics['auc_roc']:.3f}")
        
        return metrics
    
    def predict_risk(self, appointment_data: Dict) -> Dict:
        """
        Predict no-show risk for a single appointment
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features
        features_df = self.prepare_features(appointment_data)
        
        # Scale features
        features_scaled = self.scaler.transform(features_df)
        
        # Get prediction
        risk_probability = self.model.predict_proba(features_scaled)[0, 1]
        
        # Determine risk tier
        if risk_probability < 0.2:
            risk_tier = "low"
        elif risk_probability < 0.6:
            risk_tier = "medium"
        else:
            risk_tier = "high"
        
        # Get feature importance for this prediction
        feature_contributions = {}
        for i, feature_name in enumerate(self.feature_names):
            feature_contributions[feature_name] = {
                'value': features_df.iloc[0, i],
                'importance': self.model.feature_importances_[i]
            }
        
        # Sort by importance
        top_factors = sorted(
            feature_contributions.items(),
            key=lambda x: x[1]['importance'],
            reverse=True
        )[:5]
        
        return {
            'risk_score': float(risk_probability),
            'risk_tier': risk_tier,
            'confidence': float(max(risk_probability, 1 - risk_probability)),
            'top_risk_factors': [
                {
                    'factor': factor[0],
                    'value': factor[1]['value'],
                    'importance': factor[1]['importance']
                }
                for factor in top_factors
            ]
        }
    
    def save_model(self, filepath: str):
        """Save the trained model to disk"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'label_encoders': self.label_encoders
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model from disk"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.label_encoders = model_data['label_encoders']
        self.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")

# Singleton instance
risk_predictor = NoShowRiskPredictor()
