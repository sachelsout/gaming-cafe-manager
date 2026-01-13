"""Test dashboard with sample session data."""

import tkinter as tk
from pathlib import Path
import sys
from datetime import datetime, time

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.ui.main_window import MainWindow
from app.services.system_service import SystemService
from app.services.session_service import SessionService

# Initialize database
db = initialize_database()
system_service = SystemService(db)
session_service = SessionService(db)

# Create sample sessions for demonstration
print("✓ Creating sample active sessions...")

# Get some systems
systems = system_service.get_all_systems()
if len(systems) >= 2:
    # Create sample session 1
    session_id_1 = session_service.create_session(
        date=datetime.now().strftime("%Y-%m-%d"),
        customer_name="Ahmed Hassan",
        system_id=systems[0].id,  # First system
        login_time="14:30:00",
        hourly_rate=systems[0].default_hourly_rate,
        notes="PS5 gaming session"
    )
    print(f"  - Session 1 created (ID: {session_id_1}): {systems[0].system_name}")
    
    # Create sample session 2
    session_id_2 = session_service.create_session(
        date=datetime.now().strftime("%Y-%m-%d"),
        customer_name="Fatima Khan",
        system_id=systems[1].id,  # Second system
        login_time="15:15:00",
        hourly_rate=systems[1].default_hourly_rate,
        notes="PC gaming"
    )
    print(f"  - Session 2 created (ID: {session_id_2}): {systems[1].system_name}")
    
    # Mark first system as in use
    system_service.set_system_availability(systems[0].id, "In Use")
    system_service.set_system_availability(systems[1].id, "In Use")

# Create test window
root = tk.Tk()
root.title("Gaming Cafe Manager - Dashboard Test")
root.geometry("1000x700")
root.minsize(800, 600)

print("\n✓ Creating MainWindow with dashboard...")
try:
    app = MainWindow(root, db)
    print("✓ Dashboard created with:")
    print(f"  - {len(system_service.get_all_systems())} systems configured")
    print(f"  - {len(session_service.get_active_sessions())} active sessions")
    print(f"  - {len(system_service.get_systems_in_use())} systems in use")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All dashboard tests passed!")
print("Window will auto-close in 3 seconds...")

# Auto-close after 3 seconds
root.after(3000, root.quit)
root.mainloop()

print("✓ Dashboard test completed successfully!")
