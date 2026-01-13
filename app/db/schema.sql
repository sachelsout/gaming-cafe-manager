-- Gaming Cafe Manager Database Schema
-- SQLite schema for managing gaming cafe sessions

-- Systems/Consoles available in the cafe
CREATE TABLE IF NOT EXISTS systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL UNIQUE,
    system_type TEXT NOT NULL,
    default_hourly_rate REAL NOT NULL,
    availability TEXT DEFAULT 'Available' CHECK(availability IN ('Available', 'In Use')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gaming sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    customer_name TEXT NOT NULL,
    system_id INTEGER NOT NULL,
    login_time TIME NOT NULL,
    logout_time TIME,
    duration_minutes INTEGER,
    hourly_rate REAL NOT NULL,
    extra_charges REAL DEFAULT 0.0,
    total_due REAL,
    payment_status TEXT CHECK(payment_status IN ('Paid-Cash', 'Paid-Online', 'Paid-Mixed', 'Pending')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE RESTRICT
);

-- Create indices for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
CREATE INDEX IF NOT EXISTS idx_sessions_system ON sessions(system_id);
CREATE INDEX IF NOT EXISTS idx_sessions_payment ON sessions(payment_status);
CREATE INDEX IF NOT EXISTS idx_sessions_customer ON sessions(customer_name);
