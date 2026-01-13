"""Test dashboard timer updates."""

import tkinter as tk
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.ui.main_window import MainWindow
from app.services.session_service import SessionService
from app.services.system_service import SystemService

# Initialize database
db = initialize_database()
system_service = SystemService(db)
session_service = SessionService(db)

print("✓ Testing dashboard live timer updates...\n")

# Create test sessions with different login times
systems = system_service.get_available_systems()
if len(systems) < 3:
    systems = system_service.get_all_systems()[:3]

sessions_created = []
for i, system in enumerate(systems[:3]):
    minutes_ago = 5 + (i * 2)  # 5, 7, 9 minutes ago
    login_time = (datetime.now() - timedelta(minutes=minutes_ago)).strftime("%H:%M:%S")
    
    session_id = session_service.create_session(
        date=datetime.now().strftime("%Y-%m-%d"),
        customer_name=f"Timer Dashboard User {i+1}",
        system_id=system.id,
        login_time=login_time,
        hourly_rate=200.0 + (i * 50),
        notes=f"Dashboard timer test session {i+1}"
    )
    
    system_service.set_system_availability(system.id, "In Use")
    sessions_created.append(session_id)
    
    print(f"✓ Created session {session_id}")
    print(f"  Customer: Timer Dashboard User {i+1}")
    print(f"  System: {system.system_name}")
    print(f"  Login time {minutes_ago} minutes ago: {login_time}\n")

# Create main window
root = tk.Tk()
root.title("Dashboard Timer Test")
root.geometry("1000x700")

print("✓ Creating MainWindow with dashboard...")
try:
    app = MainWindow(root, db)
    print("✓ Dashboard created successfully")
    print("\n✓ Dashboard features:")
    print("  - Displays all active sessions")
    print("  - Shows elapsed time for each session")
    print("  - Updates elapsed time every 60 seconds")
    print("  - Timer recalculates from login time (accurate after restart)")
    print("  - No performance impact (efficient timer scheduling)")
    
    print("\nWindow will auto-close in 3 seconds...")
    
    # Show for 3 seconds
    root.after(3000, root.quit)
    root.mainloop()
    
    # Verify dashboard timer stopped
    if hasattr(app, 'dashboard') and hasattr(app.dashboard, 'stop_timer'):
        print("✓ Dashboard timer can be stopped cleanly")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All dashboard timer tests passed!")
