-- SmartShare Database Schema (MySQL Compatible)
-- Unattended Multi-Resource Allocation and Operational Governance Engine

CREATE DATABASE IF NOT EXISTS smartshare;
USE smartshare;

-- 1. Users Table (Tenant Profiles & Persistent Ledger)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    room_number VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    total_weekly_credits INT DEFAULT 15,
    remaining_credits INT DEFAULT 15,
    karma_score INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Master Resource Configuration Catalog
CREATE TABLE IF NOT EXISTS resources (
    resource_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Appliances', 'Sports', 'Rooms'
    slot_type VARCHAR(20) NOT NULL, -- 'VARIABLE_CYCLE' or 'FIXED_BLOCK'
    default_duration_mins INT NOT NULL,
    buffer_mins INT NOT NULL,
    capacity INT NOT NULL,
    base_credits INT DEFAULT 1,
    overstay_rate_per_min INT DEFAULT 10, -- Fee in INR/min
    operating_start_hour INT DEFAULT 6,    -- 06:00
    operating_end_hour INT DEFAULT 23      -- 23:00
);

-- 3. Bookings & State Machine
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    resource_id VARCHAR(20) NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_mins INT NOT NULL,
    credits_charged INT NOT NULL,
    is_consecutive_surge BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'CONFIRMED', -- 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'RELEASED_EARLY', 'CANCELLED', 'NO_SHOW'
    check_in_time TIMESTAMP NULL,
    actual_end_time TIMESTAMP NULL,
    custody_accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

-- 4. Incidents & Rent-Demerit Ledger
CREATE TABLE IF NOT EXISTS incidents (
    incident_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    offending_user_id INT NOT NULL,
    reported_by_user_id INT NOT NULL,
    resource_id VARCHAR(20) NOT NULL,
    incident_type VARCHAR(50) NOT NULL, -- 'OVERSTAY_COURT', 'UNCOLLECTED_HAMPER_ITEMS', 'UNAUTHORIZED_WALKIN', 'DAMAGE_REPORT'
    minutes_overstayed INT DEFAULT 0,
    rent_demerit_fee INT DEFAULT 0,    -- Amount in INR added to PG monthly rent bill
    bounty_credits_awarded INT DEFAULT 0, -- Credits given to reporter
    incident_notes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offending_user_id) REFERENCES users(user_id),
    FOREIGN KEY (reported_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

-- 5. Tenant Survey Response Store
CREATE TABLE IF NOT EXISTS survey_responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    respondent_name VARCHAR(100),
    room_number VARCHAR(20),
    primary_frustration VARCHAR(255),
    laundry_frequency_per_week INT,
    preferred_days VARCHAR(100),
    experienced_walkin_poaching BOOLEAN,
    experienced_clothes_abandoned BOOLEAN,
    willingness_offpeak_incentives INT, -- 1 to 5 scale
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
