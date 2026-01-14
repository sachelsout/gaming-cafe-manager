#!/usr/bin/env python3
"""Quick test to verify create_session compatibility"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.services.session_service import SessionService
from datetime import datetime

# Initialize
db = initialize_database()
session_service = SessionService(db)

# Test the old create_session method
try:
    session_id = session_service.create_session(
        date=datetime.now().strftime("%Y-%m-%d"),
        customer_name="Test User",
        system_id=1,
        login_time="14:30:00",
        hourly_rate=100.0,
        notes="Test"
    )
    print(f"[OK] create_session() compatibility wrapper works!")
    print(f"[OK] Created session ID: {session_id}")
    
    # Verify the session was created and started
    session = session_service.get_session_by_id(session_id)
    if session:
        print(f"[OK] Session state: {session.session_state}")
        print(f"[OK] Login time: {session.login_time}")
        if session.session_state == "ACTIVE" and session.login_time == "14:30:00":
            print("[OK] Compatibility wrapper working correctly - session created and started!")
        else:
            print("[FAIL] Session state or login time incorrect")
    else:
        print("[FAIL] Could not fetch session")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
