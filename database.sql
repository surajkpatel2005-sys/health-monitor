-- ==========================================================
-- PERSONAL HEALTH & WELLNESS MONITORING SYSTEM
-- Database Schema (MySQL)
-- ==========================================================

CREATE DATABASE IF NOT EXISTS health_monitor_db;
USE health_monitor_db;

-- ----------------------------------------------------------
-- 1. USERS TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    profile_picture VARCHAR(255) DEFAULT 'default.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------
-- 2. HEALTH PROFILE TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS health_profile (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    height FLOAT DEFAULT NULL COMMENT 'in cm',
    weight FLOAT DEFAULT NULL COMMENT 'in kg',
    medical_conditions TEXT,
    fitness_goal VARCHAR(255),
    water_goal_ml INT DEFAULT 2000,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------
-- 3. BMI RECORDS TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS bmi_records (
    bmi_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    bmi_value FLOAT NOT NULL,
    bmi_category VARCHAR(30) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------
-- 4. WATER TRACKER TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS water_tracker (
    water_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount_ml INT NOT NULL,
    log_date DATE NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------
-- 5. WEIGHT TRACKER TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS weight_tracker (
    weight_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    weight FLOAT NOT NULL,
    log_date DATE NOT NULL,
    notes VARCHAR(255),
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------
-- 6. SLEEP TRACKER TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS sleep_tracker (
    sleep_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    sleep_time TIME NOT NULL,
    wake_time TIME NOT NULL,
    duration_hours FLOAT NOT NULL,
    log_date DATE NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------
-- 7. EXERCISE TRACKER TABLE
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS exercise_tracker (
    exercise_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    exercise_name VARCHAR(100) NOT NULL,
    duration_minutes INT NOT NULL,
    calories_burned FLOAT NOT NULL,
    log_date DATE NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------
-- INDEXES FOR PERFORMANCE
-- ----------------------------------------------------------
CREATE INDEX idx_bmi_user ON bmi_records(user_id);
CREATE INDEX idx_water_user_date ON water_tracker(user_id, log_date);
CREATE INDEX idx_weight_user ON weight_tracker(user_id);
CREATE INDEX idx_sleep_user ON sleep_tracker(user_id);
CREATE INDEX idx_exercise_user ON exercise_tracker(user_id);
