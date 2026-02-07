-- Medication Adherence Support System Database Schema

-- Users/Patients Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    date_of_birth DATE,
    gender VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical History/Allergies Table
CREATE TABLE IF NOT EXISTS user_medical_info (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    drug_allergies TEXT,
    food_allergies TEXT,
    existing_conditions TEXT,
    current_medications TEXT,
    is_pregnant BOOLEAN DEFAULT FALSE,
    is_breastfeeding BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medications Database (Reference)
CREATE TABLE IF NOT EXISTS medications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    generic_name VARCHAR(255),
    description TEXT,
    common_side_effects TEXT,
    how_it_works TEXT,
    plain_language_explanation TEXT,
    contraindications TEXT,
    storage_instructions TEXT,
    manufacturer VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prescriptions Table
CREATE TABLE IF NOT EXISTS prescriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    medication_id INTEGER REFERENCES medications(id),
    medicine_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    dosage_unit VARCHAR(50),
    frequency VARCHAR(100) NOT NULL,
    duration INTEGER, -- in days
    start_date DATE NOT NULL,
    end_date DATE,
    route VARCHAR(50), -- oral, injection, etc.
    instructions TEXT,
    special_instructions TEXT,
    prescribed_by VARCHAR(255),
    prescription_image_url VARCHAR(500),
    ocr_confidence FLOAT,
    is_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adherence Plan Table
CREATE TABLE IF NOT EXISTS adherence_plans (
    id SERIAL PRIMARY KEY,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    daily_schedule TEXT[], -- array of dose times
    why_important TEXT,
    nudge_reason TEXT,
    completion_percentage FLOAT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dose Tracking Table
CREATE TABLE IF NOT EXISTS dose_tracking (
    id SERIAL PRIMARY KEY,
    adherence_plan_id INTEGER NOT NULL REFERENCES adherence_plans(id) ON DELETE CASCADE,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP NOT NULL,
    actual_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending', -- pending, taken, missed, skipped
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contraindication Check Results Table
CREATE TABLE IF NOT EXISTS contraindication_checks (
    id SERIAL PRIMARY KEY,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    medication_name VARCHAR(255),
    check_type VARCHAR(100), -- allergy, interaction, condition-based
    risk_level VARCHAR(50), -- low, medium, high
    warning_message TEXT,
    recommendation TEXT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reminders/Notifications Table
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    dose_tracking_id INTEGER NOT NULL REFERENCES dose_tracking(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_text TEXT,
    reminder_time TIMESTAMP NOT NULL,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    reminder_method VARCHAR(50), -- app, email, sms
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adherence Summary Table (Daily/Weekly aggregation)
CREATE TABLE IF NOT EXISTS adherence_summary (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_doses INTEGER DEFAULT 0,
    doses_taken INTEGER DEFAULT 0,
    doses_missed INTEGER DEFAULT 0,
    adherence_percentage FLOAT DEFAULT 0,
    week_of_month VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Caregiver Access Table
CREATE TABLE IF NOT EXISTS caregiver_access (
    id SERIAL PRIMARY KEY,
    patient_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    caregiver_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_level VARCHAR(50) DEFAULT 'view', -- view, manage
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(patient_user_id, caregiver_user_id)
);

-- Doctor/Healthcare Provider Contact Table
CREATE TABLE IF NOT EXISTS healthcare_providers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_name VARCHAR(255),
    provider_type VARCHAR(100),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    specialization VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_user_prescriptions ON prescriptions(user_id);
CREATE INDEX idx_prescription_medication ON prescriptions(medication_id);
CREATE INDEX idx_dose_tracking_user ON dose_tracking(user_id);
CREATE INDEX idx_dose_tracking_date ON dose_tracking(scheduled_time);
CREATE INDEX idx_adherence_summary_user_date ON adherence_summary(user_id, date);
CREATE INDEX idx_contraindication_prescription ON contraindication_checks(prescription_id);
CREATE INDEX idx_reminders_sent ON reminders(is_sent);
