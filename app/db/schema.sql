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

-- Gaming sessions with prepaid-first model
-- Session states: PLANNED -> ACTIVE -> COMPLETED
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    customer_name TEXT NOT NULL,
    system_id INTEGER NOT NULL,
    session_state TEXT DEFAULT 'PLANNED' CHECK(session_state IN ('PLANNED', 'ACTIVE', 'COMPLETED')),
    planned_duration_min INTEGER NOT NULL,
    login_time TIME,
    logout_time TIME,
    actual_duration_min INTEGER,
    hourly_rate REAL NOT NULL,
    paid_amount REAL NOT NULL,
    extra_charges REAL DEFAULT 0.0,
    total_due REAL NOT NULL,
    payment_method TEXT NOT NULL CHECK(payment_method IN ('Cash', 'Online', 'Mixed')),
    payment_status TEXT DEFAULT 'PAID' CHECK(payment_status IN ('PAID', 'Pending', 'Refunded')),
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
