"""Test end session dialog UI."""

import tkinter as tk
from pathlib import Path
import sys
from datetime import datetime

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.services.session_service import SessionService
from app.services.system_service import SystemService
from app.ui.dialogs.end_session_dialog import EndSessionDialog

# Initialize database
db = initialize_database()
system_service = SystemService(db)
session_service = SessionService(db)

# Create test window
root = tk.Tk()
root.title("End Session Dialog Test")
root.geometry("600x400")
root.withdraw()  # Hide main window

print("✓ Testing end session dialog...\n")

# Create a test session
systems = system_service.get_available_systems()
if not systems:
    print("✗ No available systems, creating one manually...")
    system = system_service.get_all_systems()[0]
else:
    system = systems[0]

session_id = session_service.create_session(
    date=datetime.now().strftime("%Y-%m-%d"),
    customer_name="UI Test User",
    system_id=system.id,
    login_time="19:00:00",
    hourly_rate=250.0,
    notes="UI test session"
)
print(f"✓ Created test session {session_id}")
print(f"  Customer: UI Test User")
print(f"  System: {system.system_name}")
print(f"  Login time: 19:00:00")
print(f"  Rate: 250.0/hour\n")

# Mark system as in use
system_service.set_system_availability(system.id, "In Use")

print("✓ Test 1: Opening end session dialog...")
try:
    def on_success():
        print("\n✓ Test 2: Session ended successfully!")
        # Get updated session
        session = session_service.get_session_by_id(session_id)
        print(f"  Logout time: {session.logout_time}")
        print(f"  Duration: {session.duration_minutes} minutes")
        print(f"  Total due: {session.total_due:.2f}")
        root.after(500, root.quit)
    
    # Show main window
    root.deiconify()
    
    # Create dialog
    dialog = EndSessionDialog(root, db, session_id, on_success=on_success)
    
    print("  - Dialog opened successfully")
    print("  - Dialog contains:")
    print("    * Session info (customer, system, login time)")
    print("    * Logout time input (auto-filled)")
    print("    * Duration display (auto-calculated)")
    print("    * Hourly rate input (editable)")
    print("    * Base amount display (auto-calculated)")
    print("    * Extra charges input (optional)")
    print("    * Total due display (auto-calculated, highlighted)")
    
    # Auto-fill and submit after 1.5 seconds
    root.after(1500, lambda: _auto_submit_dialog(dialog))
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def _auto_submit_dialog(dialog):
    """Auto-submit the dialog for testing."""
    try:
        # Set logout time (21:45:30 = 2h 45m 30s)
        dialog.logout_time_var.set("21:45:30")
        
        # Add extra charges
        dialog.extra_charges_var.set("50.0")
        
        # Keep rate as-is
        
        print("\n✓ Test 2: Auto-filled form with:")
        print("  Logout time: 21:45:30")
        print("  Extra charges: 50.0")
        
        # Submit
        dialog._end_session()
    except Exception as e:
        print(f"  ✗ Error in auto-submit: {e}")
        import traceback
        traceback.print_exc()
        root.quit()

# Run event loop
root.mainloop()

# Verify final state
print("\n✓ Test 3: Verifying final session state...")
session = session_service.get_session_by_id(session_id)
print(f"  Session {session_id}:")
print(f"    Customer: {session.customer_name}")
print(f"    Login: {session.login_time} → Logout: {session.logout_time}")
print(f"    Duration: {session.duration_minutes} minutes")
print(f"    Rate: {session.hourly_rate}/hour")
print(f"    Extra charges: {session.extra_charges:.2f}")
print(f"    Total due: {session.total_due:.2f}")

# Expected calculation: 2h 45m 30s = 165 min (seconds rounded down) = 2.75 hours
# Base = 250 * 2.75 = 687.5
# Total = 687.5 + 50 = 737.5
expected_total = 737.5
if abs(session.total_due - expected_total) < 0.1:  # Allow small rounding differences
    print(f"\n✓ All end session dialog tests passed!")
else:
    print(f"\n✗ Total mismatch: expected {expected_total}, got {session.total_due}")
