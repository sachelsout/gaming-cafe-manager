#!/usr/bin/env python3
"""Test end_session method call"""

import sys
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.services.session_service import SessionService

# Initialize
db = initialize_database()
session_service = SessionService(db)

# Create a test session
session_id = session_service.create_session(
    date=datetime.now().strftime("%Y-%m-%d"),
    customer_name="Test User",
    system_id=1,
    login_time="14:30:00",
    hourly_rate=100.0,
    notes="Test"
)

print(f"[OK] Created session {session_id}")

# Test the new end_session method with correct arguments
try:
    success = session_service.end_session(
        session_id,
        logout_time="15:45:00",
        extra_charges=50.0,
        notes="Test ended"
    )
    
    if success:
        print("[OK] end_session() called successfully with new signature!")
        
        # Verify the session was updated
        session = session_service.get_session_by_id(session_id)
        if session:
            print(f"[OK] Session state: {session.session_state}")
            print(f"[OK] Actual duration: {session.actual_duration_min} minutes")
            print(f"[OK] Logout time: {session.logout_time}")
            print(f"[OK] Extra charges: {session.extra_charges}")
        else:
            print("[FAIL] Could not fetch session")
    else:
        print("[FAIL] end_session returned False")
except TypeError as e:
    print(f"[FAIL] TypeError: {e}")
except Exception as e:
    print(f"[FAIL] Exception: {e}")
    import traceback
    traceback.print_exc()
