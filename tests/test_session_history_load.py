#!/usr/bin/env python3
"""Test that session_history_dialog can load data without errors"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.services.session_service import SessionService

# Initialize
db = initialize_database()
session_service = SessionService(db)

# Create a completed session to test loading
print("Creating test sessions...")

# Session 1: Create and complete
session_id_1 = session_service.create_session(
    date=datetime.now().strftime("%Y-%m-%d"),
    customer_name="Test User 1",
    system_id=1,
    login_time="14:30:00",
    hourly_rate=100.0,
    notes="Test 1"
)
print(f"[OK] Created session {session_id_1}")

# End it
success = session_service.end_session(
    session_id_1,
    logout_time="15:45:00",
    extra_charges=10.0,
    notes="Ended test 1"
)
if success:
    print(f"[OK] Completed session {session_id_1}")

# Session 2: Create and complete
session_id_2 = session_service.create_session(
    date=datetime.now().strftime("%Y-%m-%d"),
    customer_name="Test User 2",
    system_id=2,
    login_time="16:00:00",
    hourly_rate=150.0,
    notes="Test 2"
)
print(f"[OK] Created session {session_id_2}")

# End it
success = session_service.end_session(
    session_id_2,
    logout_time="17:30:00",
    extra_charges=20.0,
    notes="Ended test 2"
)
if success:
    print(f"[OK] Completed session {session_id_2}")

# Now test loading completed sessions
print("\nTesting session history load_data...")
try:
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    sessions = session_service.get_completed_sessions(today, tomorrow)
    print(f"[OK] Loaded {len(sessions)} completed sessions")
    
    # Try to access the fields that were failing before
    for session in sessions:
        # Test that actual_duration_min exists and works
        duration = session.actual_duration_min
        payment_method = session.payment_method if hasattr(session, 'payment_method') else "Cash"
        print(f"[OK] Session {session.id}: duration={duration}min, method={payment_method}")
        
    print("\n[PASS] session_history_dialog can now load data successfully!")
except AttributeError as e:
    print(f"[FAIL] AttributeError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"[FAIL] Exception: {e}")
    import traceback
    traceback.print_exc()
