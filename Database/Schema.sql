-- ==========================================
-- Crime Intelligence Platform Database
-- Part 1 - Foundation Tables
-- ==========================================

-- Create Database (Skip if already created)
CREATE DATABASE IF NOT EXISTS crime_intelligence;
USE crime_intelligence;

-- ==========================================
-- ROLES
-- ==========================================

CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- USERS
-- ==========================================

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_role
        FOREIGN KEY (role_id)
        REFERENCES roles(role_id)
        ON DELETE SET NULL
);

-- ==========================================
-- OFFICERS
-- ==========================================

CREATE TABLE officers (
    officer_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    badge_number VARCHAR(30) UNIQUE NOT NULL,
    designation VARCHAR(100),
    department VARCHAR(100),
    police_station VARCHAR(150),
    joining_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_officer_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX idx_users_email
ON users(email);

CREATE INDEX idx_officer_badge
ON officers(badge_number);

-- ==========================================
-- PART 2 : LOCATIONS, CRIME TYPES & FIRS
-- ==========================================

-- ==========================================
-- LOCATIONS
-- ==========================================

CREATE TABLE locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,

    district VARCHAR(100) NOT NULL,

    city VARCHAR(100) NOT NULL,

    area VARCHAR(150) NOT NULL,

    pincode VARCHAR(10),

    latitude DECIMAL(10,8),

    longitude DECIMAL(11,8),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- CRIME TYPES
-- ==========================================

CREATE TABLE crime_types (

    crime_type_id INT AUTO_INCREMENT PRIMARY KEY,

    crime_name VARCHAR(100) NOT NULL,

    category VARCHAR(100),

    severity ENUM('Low','Medium','High','Critical'),

    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- FIRS
-- ==========================================

CREATE TABLE firs (

    fir_id INT AUTO_INCREMENT PRIMARY KEY,

    fir_number VARCHAR(50) UNIQUE NOT NULL,

    crime_type_id INT NOT NULL,

    location_id INT NOT NULL,

    officer_id INT,

    title VARCHAR(255),

    description TEXT,

    incident_date DATETIME NOT NULL,

    complaint_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    investigation_status ENUM(
        'Pending',
        'Under Investigation',
        'Solved',
        'Closed'
    ) DEFAULT 'Pending',

    priority ENUM(
        'Low',
        'Medium',
        'High',
        'Critical'
    ) DEFAULT 'Medium',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (crime_type_id)
        REFERENCES crime_types(crime_type_id),

    FOREIGN KEY (location_id)
        REFERENCES locations(location_id),

    FOREIGN KEY (officer_id)
        REFERENCES officers(officer_id)
);

-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX idx_fir_number
ON firs(fir_number);

CREATE INDEX idx_incident_date
ON firs(incident_date);

CREATE INDEX idx_city
ON locations(city);

CREATE INDEX idx_crime_name
ON crime_types(crime_name);

-- ==========================================
-- PART 3 : ACCUSED, VICTIMS & EVIDENCE
-- ==========================================

-- ==========================================
-- ACCUSED
-- ==========================================

CREATE TABLE accused (

    accused_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    age INT,

    gender ENUM('Male','Female','Other'),

    dob DATE,

    phone VARCHAR(20),

    email VARCHAR(100),

    address TEXT,

    occupation VARCHAR(100),

    aadhaar_number VARCHAR(20),

    risk_score DECIMAL(5,2) DEFAULT 0,

    is_repeat_offender BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- VICTIMS
-- ==========================================

CREATE TABLE victims (

    victim_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    age INT,

    gender ENUM('Male','Female','Other'),

    phone VARCHAR(20),

    email VARCHAR(100),

    address TEXT,

    occupation VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- FIR ↔ ACCUSED (Many-to-Many)
-- ==========================================

CREATE TABLE fir_accused (

    fir_id INT,

    accused_id INT,

    PRIMARY KEY (fir_id, accused_id),

    FOREIGN KEY (fir_id)
        REFERENCES firs(fir_id)
        ON DELETE CASCADE,

    FOREIGN KEY (accused_id)
        REFERENCES accused(accused_id)
        ON DELETE CASCADE
);

-- ==========================================
-- FIR ↔ VICTIMS (Many-to-Many)
-- ==========================================

CREATE TABLE fir_victims (

    fir_id INT,

    victim_id INT,

    PRIMARY KEY (fir_id, victim_id),

    FOREIGN KEY (fir_id)
        REFERENCES firs(fir_id)
        ON DELETE CASCADE,

    FOREIGN KEY (victim_id)
        REFERENCES victims(victim_id)
        ON DELETE CASCADE
);

-- ==========================================
-- EVIDENCE
-- ==========================================

CREATE TABLE evidence (

    evidence_id INT AUTO_INCREMENT PRIMARY KEY,

    fir_id INT NOT NULL,

    evidence_type ENUM(
        'Photo',
        'Video',
        'Document',
        'Fingerprint',
        'DNA',
        'Weapon',
        'Digital',
        'Other'
    ),

    evidence_name VARCHAR(200),

    description TEXT,

    file_path VARCHAR(255),

    collected_by INT,

    collected_date DATETIME,

    FOREIGN KEY (fir_id)
        REFERENCES firs(fir_id)
        ON DELETE CASCADE,

    FOREIGN KEY (collected_by)
        REFERENCES officers(officer_id)
        ON DELETE SET NULL
);

-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX idx_accused_name
ON accused(full_name);

CREATE INDEX idx_victim_name
ON victims(full_name);

CREATE INDEX idx_evidence_type
ON evidence(evidence_type);

-- ==========================================
-- PART 4 : AI & INTELLIGENCE TABLES
-- ==========================================

-- ==========================================
-- CRIME HISTORY
-- ==========================================

CREATE TABLE crime_history (

    history_id INT AUTO_INCREMENT PRIMARY KEY,

    accused_id INT NOT NULL,

    fir_id INT,

    crime_type VARCHAR(100),

    arrest_date DATE,

    conviction_status ENUM(
        'Pending',
        'Convicted',
        'Acquitted'
    ) DEFAULT 'Pending',

    sentence TEXT,

    remarks TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (accused_id)
        REFERENCES accused(accused_id)
        ON DELETE CASCADE,

    FOREIGN KEY (fir_id)
        REFERENCES firs(fir_id)
        ON DELETE SET NULL
);

-- ==========================================
-- FINANCIAL TRANSACTIONS
-- ==========================================

CREATE TABLE financial_transactions (

    transaction_id INT AUTO_INCREMENT PRIMARY KEY,

    accused_id INT,

    fir_id INT,

    bank_name VARCHAR(100),

    account_number VARCHAR(50),

    transaction_reference VARCHAR(100),

    amount DECIMAL(15,2),

    transaction_type ENUM(
        'Credit',
        'Debit'
    ),

    transaction_date DATETIME,

    remarks TEXT,

    FOREIGN KEY (accused_id)
        REFERENCES accused(accused_id)
        ON DELETE SET NULL,

    FOREIGN KEY (fir_id)
        REFERENCES firs(fir_id)
        ON DELETE SET NULL
);

-- ==========================================
-- CONVERSATION HISTORY
-- ==========================================

CREATE TABLE conversation_history (

    conversation_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT,

    question TEXT,

    ai_response LONGTEXT,

    language VARCHAR(20),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

-- ==========================================
-- AUDIT LOGS
-- ==========================================

CREATE TABLE audit_logs (

    log_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT,

    action VARCHAR(255),

    table_name VARCHAR(100),

    record_id INT,

    ip_address VARCHAR(50),

    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

-- ==========================================
-- PREDICTIONS
-- ==========================================

CREATE TABLE predictions (

    prediction_id INT AUTO_INCREMENT PRIMARY KEY,

    location_id INT,

    crime_type_id INT,

    prediction_date DATE,

    predicted_cases INT,

    confidence_score DECIMAL(5,2),

    risk_level ENUM(
        'Low',
        'Medium',
        'High',
        'Critical'
    ),

    generated_by VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (location_id)
        REFERENCES locations(location_id)
        ON DELETE SET NULL,

    FOREIGN KEY (crime_type_id)
        REFERENCES crime_types(crime_type_id)
        ON DELETE SET NULL
);

-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX idx_history_accused
ON crime_history(accused_id);

CREATE INDEX idx_transaction_accused
ON financial_transactions(accused_id);

CREATE INDEX idx_prediction_location
ON predictions(location_id);

CREATE INDEX idx_prediction_date
ON predictions(prediction_date);

CREATE INDEX idx_conversation_user
ON conversation_history(user_id);

CREATE INDEX idx_audit_user
ON audit_logs(user_id);