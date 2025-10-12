/**
 * Integrated Healthcare System JavaScript
 * Connects frontend with Phase 1 + Phase 2 backends
 */

// API Configuration
const PHASE1_API = 'http://localhost:3000/api/v1';
const PHASE2_API = 'http://localhost:8000/api/v1';

// Global state
let currentTriageData = {};
let recentActivities = [];

// Common symptoms for triage
const commonSymptoms = [
    'Abdominal pain', 'Back pain', 'Bleeding', 'Bloating', 'Breast changes',
    'Chest pain', 'Constipation', 'Cough', 'Diarrhea', 'Dizziness',
    'Fatigue', 'Fever', 'Headache', 'Irregular periods', 'Joint pain',
    'Mood changes', 'Nausea', 'Pelvic pain', 'Rash', 'Shortness of breath',
    'Sleep problems', 'Swelling', 'Urinary issues', 'Vaginal discharge', 'Weight changes'
];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupSymptomGrid();
    setupEventListeners();
    checkSystemHealth();
    setDefaultDateTime();
}

function setupSymptomGrid() {
    const grid = document.getElementById('symptomGrid');
    grid.innerHTML = commonSymptoms.map(symptom => `
        <div class="symptom-checkbox" onclick="toggleSymptom('${symptom}')">
            <input type="checkbox" id="symptom-${symptom.replace(/\s+/g, '-')}" />
            <label for="symptom-${symptom.replace(/\s+/g, '-')}">${symptom}</label>
        </div>
    `).join('');
}

function setupEventListeners() {
    // Triage form
    document.getElementById('triageForm').addEventListener('submit', handleTriageSubmission);
    
    // Scheduling form
    document.getElementById('schedulingForm').addEventListener('submit', handleSchedulingSubmission);
    
    // Registration forms
    document.getElementById('doctorRegistrationForm').addEventListener('submit', handleDoctorRegistration);
    document.getElementById('patientRegistrationForm').addEventListener('submit', handlePatientRegistration);
}

function setDefaultDateTime() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    document.getElementById('preferredDate').value = tomorrow.toISOString().slice(0, 16);
}

// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Add active class to clicked nav tab
    event.target.classList.add('active');
}

// Symptom selection
function toggleSymptom(symptom) {
    const checkbox = document.getElementById(`symptom-${symptom.replace(/\s+/g, '-')}`);
    const container = checkbox.parentElement;
    
    checkbox.checked = !checkbox.checked;
    container.classList.toggle('selected', checkbox.checked);
}

function getSelectedSymptoms() {
    return commonSymptoms.filter(symptom => {
        const checkbox = document.getElementById(`symptom-${symptom.replace(/\s+/g, '-')}`);
        return checkbox && checkbox.checked;
    });
}

// API Helper Functions
async function makeAPIRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Triage Functions
async function handleTriageSubmission(e) {
    e.preventDefault();
    
    const formData = {
        patient_id: document.getElementById('patientId').value,
        chief_complaint: document.getElementById('chiefComplaint').value,
        symptoms: getSelectedSymptoms(),
        medical_history: document.getElementById('medicalHistory').value.split(',').map(s => s.trim()).filter(s => s),
        pain_level: document.getElementById('painLevel').value ? parseInt(document.getElementById('painLevel').value) : null,
        duration_of_symptoms: document.getElementById('duration').value || null,
        current_medications: [],
        allergies: []
    };
    
    try {
        showLoading('triageResults');
        const result = await makeAPIRequest(`${PHASE1_API}/triage/assess`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        currentTriageData = result;
        displayTriageResults(result);
        addActivity(`Triage completed: ${result.priority_level.toUpperCase()} priority`);
        
        // Auto-fill scheduling form
        document.getElementById('schedulePatientId').value = formData.patient_id;
        document.getElementById('triageId').value = result.triage_id;
        
    } catch (error) {
        showError('triageResults', 'Triage assessment failed: ' + error.message);
    }
}

function displayTriageResults(result) {
    const resultsDiv = document.getElementById('triageResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.className = 'results success';
    
    const priorityBadge = `<span class="priority-badge priority-${result.priority_level}">${result.priority_level.toUpperCase()}</span>`;
    
    resultsDiv.innerHTML = `
        <h3>🎯 AI Triage Assessment Complete</h3>
        <div class="appointment-card">
            <div class="appointment-header">
                <strong>Assessment Results</strong>
                ${priorityBadge}
            </div>
            <p><strong>🏥 Recommended Specialty:</strong> ${result.recommended_specialty}</p>
            <p><strong>⏰ Timeline:</strong> ${result.urgency_timeline}</p>
            <p><strong>👨‍⚕️ Doctor Visit Needed:</strong> ${result.doctor_visit_needed ? 'Yes' : 'No'}</p>
            <p><strong>🔬 Recommended Procedure:</strong> ${result.recommended_procedure}</p>
            <p><strong>⏱️ Estimated Duration:</strong> ${result.estimated_appointment_duration} minutes</p>
            ${result.red_flag_symptoms && result.red_flag_symptoms.length > 0 ? 
                `<p><strong>🚨 Red Flag Symptoms:</strong> ${result.red_flag_symptoms.join(', ')}</p>` : ''}
            <p><strong>📋 Next Steps:</strong> ${result.next_steps}</p>
            <p><strong>🆔 Triage ID:</strong> <code>${result.triage_id}</code></p>
        </div>
    `;
    
    updateRecentTriages(result);
}

// Scheduling Functions
async function handleSchedulingSubmission(e) {
    e.preventDefault();
    
    const formData = {
        patient_id: document.getElementById('schedulePatientId').value,
        triage_id: document.getElementById('triageId').value,
        preferred_datetime: document.getElementById('preferredDate').value ? 
            new Date(document.getElementById('preferredDate').value).toISOString() : null,
        telehealth_preferred: document.getElementById('telehealthPreferred').checked,
        insurance_provider: document.getElementById('insuranceProvider').value,
        special_requirements: null
    };
    
    try {
        showLoading('schedulingResults');
        const result = await makeAPIRequest(`${PHASE1_API}/appointments/schedule`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        displaySchedulingResults(result);
        addActivity(`Appointment scheduled: ${result.confirmation_number}`);
        
    } catch (error) {
        showError('schedulingResults', 'Appointment scheduling failed: ' + error.message);
    }
}

function displaySchedulingResults(result) {
    const resultsDiv = document.getElementById('schedulingResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.className = 'results success';
    
    const appointmentDate = new Date(result.appointment_datetime).toLocaleString();
    const priorityBadge = `<span class="priority-badge priority-${result.priority_level}">${result.priority_level.toUpperCase()}</span>`;
    
    resultsDiv.innerHTML = `
        <h3>✅ Appointment Scheduled Successfully</h3>
        <div class="appointment-card">
            <div class="appointment-header">
                <strong>${result.patient_name}</strong>
                ${priorityBadge}
            </div>
            <p><strong>👨‍⚕️ Doctor:</strong> ${result.doctor_name}</p>
            <p><strong>📅 Date & Time:</strong> ${appointmentDate}</p>
            <p><strong>📍 Location:</strong> ${result.location}</p>
            <p><strong>🎫 Confirmation:</strong> ${result.confirmation_number}</p>
            <p><strong>💻 Telehealth:</strong> ${result.telehealth ? 'Yes' : 'No'}</p>
            ${result.preparation_instructions ? 
                `<p><strong>📋 Instructions:</strong> ${result.preparation_instructions}</p>` : ''}
            <p><strong>🆔 Appointment ID:</strong> <code>${result.appointment_id}</code></p>
        </div>
        <div style="margin-top: 1rem;">
            <button class="btn btn-secondary" onclick="checkNoShowRiskForAppointment('${result.appointment_id}')">
                🎯 Check No-Show Risk
            </button>
        </div>
    `;
}

// Provider matching
async function findProviders() {
    try {
        showLoading('providerResults');
        const result = await makeAPIRequest(`${PHASE1_API}/providers/match`, {
            method: 'POST',
            body: JSON.stringify({
                specialty: 'Obstetrics and Gynecology',
                insurance_provider: 'Aetna',
                telehealth_ok: true
            })
        });
        
        displayProviders(result);
        
    } catch (error) {
        showError('providerResults', 'Failed to find providers: ' + error.message);
    }
}

function displayProviders(providers) {
    const resultsDiv = document.getElementById('providerResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.className = 'results';
    
    if (providers.length === 0) {
        resultsDiv.innerHTML = '<p>No matching providers found</p>';
        return;
    }
    
    let html = `<h3>👥 Found ${providers.length} Matching Providers</h3>`;
    
    providers.forEach(provider => {
        html += `
            <div class="appointment-card">
                <div class="appointment-header">
                    <strong>${provider.doctor_name}</strong>
                    <span style="background: #667eea; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">
                        ${(provider.match_score * 100).toFixed(0)}% Match
                    </span>
                </div>
                <p><strong>🏥 Specialty:</strong> ${provider.specialty}</p>
                <p><strong>📍 Location:</strong> ${provider.location}</p>
                <p><strong>📅 Available Slots:</strong> ${provider.available_slots.length}</p>
                <p><strong>⏰ Next Available:</strong> ${new Date(provider.next_available).toLocaleString()}</p>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}

// No-Show Prevention Functions
async function checkNoShowRisk() {
    const appointmentId = document.getElementById('appointmentId').value;
    if (!appointmentId) {
        showError('riskResults', 'Please enter an appointment ID');
        return;
    }
    
    await checkNoShowRiskForAppointment(appointmentId);
}

async function checkNoShowRiskForAppointment(appointmentId) {
    try {
        showLoading('riskResults');
        
        // Try Phase 2 first
        try {
            const phase2Result = await makeAPIRequest(`${PHASE2_API}/appointments/${appointmentId}`);
            displayNoShowRisk(phase2Result, true);
        } catch (phase2Error) {
            // Fallback to Phase 1
            const phase1Result = await makeAPIRequest(`${PHASE1_API}/appointments/${appointmentId}`);
            displayNoShowRisk(phase1Result, false);
        }
        
    } catch (error) {
        showError('riskResults', 'Failed to get risk assessment: ' + error.message);
    }
}

function displayNoShowRisk(result, hasPhase2Data) {
    const resultsDiv = document.getElementById('riskResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.className = 'results';
    
    if (hasPhase2Data && result.risk_assessment) {
        const risk = result.risk_assessment;
        const riskColor = risk.risk_tier === 'High' ? 'red' : 
                         risk.risk_tier === 'Medium' ? 'orange' : 'green';
        
        resultsDiv.innerHTML = `
            <h3>🎯 No-Show Risk Assessment</h3>
            <div class="appointment-card">
                <div class="appointment-header">
                    <strong>Risk Analysis</strong>
                    <span class="priority-badge priority-${riskColor}">${risk.risk_tier} Risk</span>
                </div>
                <p><strong>📊 Risk Score:</strong> ${(risk.risk_score * 100).toFixed(1)}%</p>
                <p><strong>🎯 Risk Tier:</strong> ${risk.risk_tier}</p>
                <p><strong>📱 Interventions:</strong> ${result.interventions ? result.interventions.length : 0} scheduled</p>
                ${result.interventions && result.interventions.length > 0 ? 
                    `<p><strong>🔄 Last Intervention:</strong> ${result.interventions[0].intervention_type}</p>` : ''}
            </div>
        `;
    } else {
        resultsDiv.innerHTML = `
            <h3>📋 Appointment Details</h3>
            <div class="appointment-card">
                <p><strong>🆔 Appointment ID:</strong> ${result.appointment.id}</p>
                <p><strong>👥 Patient:</strong> ${result.patient.demographics.first_name} ${result.patient.demographics.last_name}</p>
                <p><strong>👨‍⚕️ Doctor:</strong> ${result.doctor.full_name}</p>
                <p><strong>📅 Date:</strong> ${new Date(result.appointment.appointment_datetime).toLocaleString()}</p>
                <p><strong>⚠️ Phase 2 Status:</strong> Not integrated yet</p>
            </div>
        `;
    }
}

async function triggerInterventions() {
    const appointmentId = document.getElementById('interventionAppointmentId').value;
    if (!appointmentId) {
        showError('interventionResults', 'Please enter an appointment ID');
        return;
    }
    
    try {
        showLoading('interventionResults');
        const result = await makeAPIRequest(`${PHASE2_API}/interventions/trigger`, {
            method: 'POST',
            body: JSON.stringify({ appointment_id: appointmentId })
        });
        
        displayInterventionResults(result);
        
    } catch (error) {
        showError('interventionResults', 'Failed to trigger interventions: ' + error.message);
    }
}

function displayInterventionResults(result) {
    const resultsDiv = document.getElementById('interventionResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.className = 'results success';
    
    resultsDiv.innerHTML = `
        <h3>🚀 Interventions Triggered Successfully</h3>
        <div class="appointment-card">
            <p><strong>📱 Interventions Started:</strong> ${result.interventions_triggered || 'Multiple'}</p>
            <p><strong>⏰ Next Intervention:</strong> ${result.next_intervention_time || 'Scheduled'}</p>
            <p><strong>📊 Campaign Type:</strong> ${result.campaign_type || 'Risk-based'}</p>
        </div>
    `;
}

// Registration Functions
async function handleDoctorRegistration(e) {
    e.preventDefault();
    
    const formData = {
        email: document.getElementById('doctorEmail').value,
        password: document.getElementById('doctorPassword').value,
        full_name: document.getElementById('doctorName').value,
        specialty: document.getElementById('doctorSpecialty').value,
        credentials: ['MD'],
        accepted_insurances: ['Aetna', 'BlueCross', 'Cigna', 'UnitedHealth'],
        hospital_affiliation: 'Main Medical Center',
        phone: '555-0123',
        location: 'Main Campus'
    };
    
    try {
        showLoading('doctorRegistrationResults');
        const result = await makeAPIRequest(`${PHASE1_API}/doctors/register`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        displayRegistrationSuccess('doctorRegistrationResults', 'Doctor', result);
        document.getElementById('doctorRegistrationForm').reset();
        
    } catch (error) {
        showError('doctorRegistrationResults', 'Doctor registration failed: ' + error.message);
    }
}

async function handlePatientRegistration(e) {
    e.preventDefault();
    
    const formData = {
        email: document.getElementById('patientEmail').value,
        password: document.getElementById('patientPassword').value,
        demographics: {
            first_name: document.getElementById('patientFirstName').value,
            last_name: document.getElementById('patientLastName').value,
            date_of_birth: '1990-01-01',
            phone: document.getElementById('patientPhone').value
        },
        insurance: {
            provider: 'Aetna',
            policy_number: 'AET' + Math.random().toString(36).substr(2, 9).toUpperCase()
        },
        telehealth_preference: true,
        consents: {
            predictive_reminders: true,
            voice_follow_ups: false,
            sms_notifications: true,
            email_notifications: true
        },
        medical_history: [],
        allergies: []
    };
    
    try {
        showLoading('patientRegistrationResults');
        const result = await makeAPIRequest(`${PHASE1_API}/patients/register`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        displayRegistrationSuccess('patientRegistrationResults', 'Patient', result);
        document.getElementById('patientRegistrationForm').reset();
        
    } catch (error) {
        showError('patientRegistrationResults', 'Patient registration failed: ' + error.message);
    }
}

function displayRegistrationSuccess(elementId, type, result) {
    const resultsDiv = document.getElementById(elementId);
    resultsDiv.classList.remove('hidden');
    resultsDiv.className = 'results success';
    
    resultsDiv.innerHTML = `
        <h3>✅ ${type} Registration Successful</h3>
        <div class="appointment-card">
            <p><strong>🆔 ${type} ID:</strong> <code>${result.doctor_id || result.patient_id}</code></p>
            <p><strong>👤 Name:</strong> ${result.full_name}</p>
            <p><strong>📧 Email:</strong> ${result.email || 'Registered'}</p>
            ${result.specialty ? `<p><strong>🏥 Specialty:</strong> ${result.specialty}</p>` : ''}
            ${result.insurance_provider ? `<p><strong>🏥 Insurance:</strong> ${result.insurance_provider}</p>` : ''}
        </div>
    `;
}

// Analytics Functions
async function loadAnalytics() {
    try {
        showLoading('analyticsResults');
        
        const [phase1Analytics, phase2Analytics] = await Promise.allSettled([
            makeAPIRequest(`${PHASE1_API}/analytics/dashboard`),
            makeAPIRequest(`${PHASE2_API}/analytics/dashboard`)
        ]);
        
        displayAnalytics(
            phase1Analytics.status === 'fulfilled' ? phase1Analytics.value : null,
            phase2Analytics.status === 'fulfilled' ? phase2Analytics.value : null
        );
        
    } catch (error) {
        showError('analyticsResults', 'Failed to load analytics: ' + error.message);
    }
}

function displayAnalytics(phase1Data, phase2Data) {
    const resultsDiv = document.getElementById('analyticsResults');
    resultsDiv.classList.remove('hidden');
    resultsDiv.className = 'results';
    
    let html = '<h3>📊 System Analytics Dashboard</h3>';
    
    if (phase1Data) {
        html += `
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${phase1Data.total_appointments}</div>
                    <div class="metric-label">Total Appointments</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${phase1Data.total_doctors}</div>
                    <div class="metric-label">Registered Doctors</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${phase1Data.total_patients}</div>
                    <div class="metric-label">Registered Patients</div>
                </div>
            </div>
        `;
        
        if (phase1Data.priority_distribution) {
            html += `
                <h4>Priority Distribution</h4>
                <div class="appointment-card">
                    <p>🔴 <strong>Red (Emergency):</strong> ${phase1Data.priority_distribution.red || 0}</p>
                    <p>🟠 <strong>Orange (Urgent):</strong> ${phase1Data.priority_distribution.orange || 0}</p>
                    <p>🟡 <strong>Yellow (Routine):</strong> ${phase1Data.priority_distribution.yellow || 0}</p>
                    <p>🟢 <strong>Green (Administrative):</strong> ${phase1Data.priority_distribution.green || 0}</p>
                </div>
            `;
        }
    }
    
    if (phase2Data) {
        html += `
            <h4>No-Show Prevention Metrics</h4>
            <div class="appointment-card">
                <p><strong>📊 No-Show Rate:</strong> ${phase2Data.no_show_rate || 'N/A'}%</p>
                <p><strong>💰 Cost Savings:</strong> $${phase2Data.cost_savings || 'N/A'}</p>
                <p><strong>📱 Interventions Sent:</strong> ${phase2Data.total_interventions || 'N/A'}</p>
            </div>
        `;
    }
    
    resultsDiv.innerHTML = html;
}

// System Health Check
async function checkSystemHealth() {
    const statusDiv = document.getElementById('systemStatus');
    
    try {
        const [phase1Health, phase2Health] = await Promise.allSettled([
            fetch('http://localhost:3000/health'),
            fetch('http://localhost:8000/health')
        ]);
        
        const phase1Healthy = phase1Health.status === 'fulfilled' && phase1Health.value.ok;
        const phase2Healthy = phase2Health.status === 'fulfilled' && phase2Health.value.ok;
        
        statusDiv.innerHTML = `
            <div class="status-indicator ${phase1Healthy ? 'status-healthy' : 'status-offline'}">
                ${phase1Healthy ? '✅' : '❌'} Phase 1 (Triage & Scheduling)
            </div>
            <div class="status-indicator ${phase2Healthy ? 'status-healthy' : 'status-offline'}">
                ${phase2Healthy ? '✅' : '⚠️'} Phase 2 (No-Show Prevention)
            </div>
            <div class="status-indicator ${phase1Healthy && phase2Healthy ? 'status-healthy' : 'status-offline'}">
                ${phase1Healthy && phase2Healthy ? '🔗' : '🔌'} Integration Status
            </div>
        `;
        
    } catch (error) {
        statusDiv.innerHTML = `
            <div class="status-indicator status-offline">
                ❌ System Check Failed
            </div>
        `;
    }
}

// Utility Functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    element.classList.remove('hidden');
    element.className = 'results';
    element.innerHTML = '<div class="loading"><div class="spinner"></div><p>Processing...</p></div>';
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.classList.remove('hidden');
    element.className = 'results error';
    element.innerHTML = `<p>❌ ${message}</p>`;
}

function addActivity(activity) {
    recentActivities.unshift({
        activity: activity,
        timestamp: new Date().toLocaleString()
    });
    
    // Keep only last 5 activities
    recentActivities = recentActivities.slice(0, 5);
}

function updateRecentTriages(triageResult) {
    const container = document.getElementById('recentTriages');
    const priorityBadge = `<span class="priority-badge priority-${triageResult.priority_level}">${triageResult.priority_level.toUpperCase()}</span>`;
    
    const triageCard = document.createElement('div');
    triageCard.className = 'appointment-card';
    triageCard.innerHTML = `
        <div class="appointment-header">
            <strong>Triage Assessment</strong>
            ${priorityBadge}
        </div>
        <p><strong>🏥 Specialty:</strong> ${triageResult.recommended_specialty}</p>
        <p><strong>⏰ Timeline:</strong> ${triageResult.urgency_timeline}</p>
        <p><strong>🆔 ID:</strong> <code>${triageResult.triage_id}</code></p>
        <p><small>📅 ${new Date().toLocaleString()}</small></p>
    `;
    
    // Replace "No recent assessments" message
    if (container.innerHTML.includes('No recent assessments')) {
        container.innerHTML = '';
    }
    
    container.insertBefore(triageCard, container.firstChild);
    
    // Keep only last 3 assessments
    while (container.children.length > 3) {
        container.removeChild(container.lastChild);
    }
}
