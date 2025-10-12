-- Database integration approach
-- If Phase 1 and Phase 2 share the same database

-- Create a trigger function that calls your API when appointments are inserted
CREATE OR REPLACE FUNCTION trigger_noshow_prevention()
RETURNS TRIGGER AS $$
DECLARE
    api_url TEXT := 'http://localhost:8000/api/v1/appointments';
    payload JSON;
BEGIN
    -- Build JSON payload from the inserted appointment
    payload := json_build_object(
        'external_id', NEW.appointment_id,
        'patient_external_id', NEW.patient_id,
        'patient_first_name', (SELECT first_name FROM patients WHERE id = NEW.patient_id),
        'patient_last_name', (SELECT last_name FROM patients WHERE id = NEW.patient_id),
        'patient_phone', (SELECT phone FROM patients WHERE id = NEW.patient_id),
        'patient_email', (SELECT email FROM patients WHERE id = NEW.patient_id),
        'provider_external_id', NEW.provider_id,
        'provider_name', (SELECT name FROM providers WHERE id = NEW.provider_id),
        'appointment_datetime', NEW.appointment_datetime,
        'appointment_type', NEW.appointment_type,
        'clinical_priority', NEW.priority_level,
        'chief_complaint', NEW.chief_complaint
    );
    
    -- Call your no-show prevention API (requires pg_net extension)
    PERFORM net.http_post(
        url := api_url,
        headers := '{"Content-Type": "application/json"}'::jsonb,
        body := payload::jsonb
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on Phase 1 appointments table
CREATE TRIGGER appointment_noshow_trigger
    AFTER INSERT ON phase1_appointments
    FOR EACH ROW
    EXECUTE FUNCTION trigger_noshow_prevention();

-- Alternative: Use a queue table approach
CREATE TABLE appointment_processing_queue (
    id SERIAL PRIMARY KEY,
    appointment_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- Insert into queue when appointment created
CREATE OR REPLACE FUNCTION queue_appointment_processing()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO appointment_processing_queue (appointment_id)
    VALUES (NEW.appointment_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER queue_appointment_trigger
    AFTER INSERT ON phase1_appointments
    FOR EACH ROW
    EXECUTE FUNCTION queue_appointment_processing();
