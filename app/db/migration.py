"""Database migration script for prepaid-first session model."""

import sqlite3
from pathlib import Path
from typing import Optional


def migrate_database(db_path: Path) -> bool:
    """
    Migrate database to prepaid-first session model.
    
    This migration:
    1. Adds new columns for prepaid workflow
    2. Converts existing sessions to COMPLETED state
    3. Calculates paid_amount from total_due
    4. Sets payment_method based on old payment_status
    5. Keeps payment_status as-is (old values) to avoid CHECK constraint issues
    6. Makes system_id nullable to preserve session history when systems are deleted
    
    Args:
        db_path: Path to the database file
    
    Returns:
        True if migration successful, False if already migrated
    
    Raises:
        Exception: If migration fails
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if migration already applied
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'session_state' in columns:
            print("[INFO] Database already migrated")
            
            # Check if we need to update the foreign key constraint
            # This is done by checking if system_id is nullable
            cursor.execute("PRAGMA table_info(sessions)")
            columns = cursor.fetchall()
            system_id_col = next((col for col in columns if col[1] == 'system_id'), None)
            
            if system_id_col and system_id_col[3] == 1:  # notnull flag is 1
                print("[INFO] Updating foreign key constraint to allow NULL system_id...")
                _update_foreign_key_constraint(conn, cursor)
            
            conn.close()
            return False
        
        print("[INFO] Starting database migration for prepaid-first model...")
        
        # Add new columns (without CHECK constraints that would conflict)
        migration_steps = [
            # Add session_state column (default COMPLETED for existing sessions)
            "ALTER TABLE sessions ADD COLUMN session_state TEXT DEFAULT 'COMPLETED'",
            
            # Add planned_duration_min (use existing duration_minutes)
            "ALTER TABLE sessions ADD COLUMN planned_duration_min INTEGER",
            
            # Add actual_duration_min (use existing duration_minutes)
            "ALTER TABLE sessions ADD COLUMN actual_duration_min INTEGER",
            
            # Add paid_amount (use total_due)
            "ALTER TABLE sessions ADD COLUMN paid_amount REAL",
            
            # Add payment_method (extract from payment_status)
            "ALTER TABLE sessions ADD COLUMN payment_method TEXT",
        ]
        
        for step in migration_steps:
            try:
                cursor.execute(step)
                col_name = step.split('ADD COLUMN')[1].split()[0]
                print(f"[OK] {col_name}")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    col_name = step.split('ADD COLUMN')[1].split()[0]
                    print(f"[SKIP] Column already exists: {col_name}")
                else:
                    raise
        
        # Update payment_method from old payment_status
        print("[INFO] Converting payment_status to payment_method...")
        
        cursor.execute("SELECT DISTINCT payment_status FROM sessions WHERE payment_status IS NOT NULL")
        statuses = cursor.fetchall()
        
        for status, in statuses:
            if status is None:
                continue
            
            # Extract payment method from old status (e.g., 'Paid-Cash' -> 'Cash')
            if 'Cash' in status:
                method = 'Cash'
            elif 'Online' in status:
                method = 'Online'
            elif 'Mixed' in status:
                method = 'Mixed'
            else:
                method = 'Cash'  # Default
            
            cursor.execute(
                "UPDATE sessions SET payment_method = ? WHERE payment_status = ?",
                (method, status)
            )
            print(f"[OK] Updated {cursor.rowcount} sessions with payment method: {method}")
        
        # Set paid_amount from total_due and ensure it has a value
        print("[INFO] Setting paid_amount from total_due...")
        cursor.execute(
            "UPDATE sessions SET paid_amount = COALESCE(total_due, hourly_rate) WHERE paid_amount IS NULL"
        )
        print(f"[OK] Updated {cursor.rowcount} sessions with paid_amount")
        
        # Set planned_duration_min from duration_minutes
        print("[INFO] Setting planned_duration_min from duration_minutes...")
        cursor.execute(
            "UPDATE sessions SET planned_duration_min = COALESCE(duration_minutes, 60) WHERE planned_duration_min IS NULL"
        )
        print(f"[OK] Updated {cursor.rowcount} sessions with planned_duration_min")
        
        # Set actual_duration_min from duration_minutes
        print("[INFO] Setting actual_duration_min from duration_minutes...")
        cursor.execute(
            "UPDATE sessions SET actual_duration_min = duration_minutes WHERE actual_duration_min IS NULL"
        )
        print(f"[OK] Updated {cursor.rowcount} sessions with actual_duration_min")
        
        # Set session_state to COMPLETED for all existing sessions
        print("[INFO] Setting session_state to COMPLETED for existing sessions...")
        cursor.execute(
            "UPDATE sessions SET session_state = 'COMPLETED' WHERE session_state IS NULL OR session_state = 'COMPLETED'"
        )
        print(f"[OK] Updated {cursor.rowcount} sessions to COMPLETED state")
        
        # Set session_state to PLANNED for any sessions without login_time
        # (these will be unpaid/incomplete sessions)
        print("[INFO] Setting session_state to PLANNED for unpaid sessions...")
        cursor.execute(
            "UPDATE sessions SET session_state = 'PLANNED' WHERE login_time IS NULL AND payment_status = 'Pending'"
        )
        print(f"[OK] Updated {cursor.rowcount} sessions to PLANNED state")
        
        # Commit changes
        conn.commit()
        print("[OK] Database migration completed successfully!")
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


def check_migration_status(db_path: Path) -> dict:
    """
    Check the migration status of the database.
    
    Args:
        db_path: Path to the database file
    
    Returns:
        Dictionary with migration status information
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(sessions)")
        columns = {column[1] for column in cursor.fetchall()}
        
        status = {
            "migrated": 'session_state' in columns,
            "columns": columns,
            "new_columns": {
                "session_state": 'session_state' in columns,
                "planned_duration_min": 'planned_duration_min' in columns,
                "actual_duration_min": 'actual_duration_min' in columns,
                "paid_amount": 'paid_amount' in columns,
                "payment_method": 'payment_method' in columns,
            }
        }
        
        return status
    
    finally:
        conn.close()

def _update_foreign_key_constraint(conn: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Update foreign key constraint to allow NULL system_id.
    
    This recreates the sessions table with the updated constraint.
    SQLite doesn't support altering foreign key constraints directly,
    so we need to recreate the table.
    
    Args:
        conn: Database connection
        cursor: Database cursor
    """
    try:
        # Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Rename old table
        cursor.execute("ALTER TABLE sessions RENAME TO sessions_old")
        
        # Create new table with updated schema
        cursor.execute("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                customer_name TEXT NOT NULL,
                system_id INTEGER,
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
                FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE SET NULL
            )
        """)
        
        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO sessions 
            SELECT * FROM sessions_old
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE sessions_old")
        
        # Re-create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_system ON sessions(system_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_payment ON sessions(payment_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_customer ON sessions(customer_name)")
        
        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("[OK] Foreign key constraint updated to allow NULL system_id")
    
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to update foreign key constraint: {e}")
        raise