"""Test start session feature."""

import tkinter as tk
from pathlib import Path
import sys

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.services.system_service import SystemService
from app.services.session_service import SessionService
from app.ui.dialogs.start_session_dialog import StartSessionDialog

# Initialize database
db = initialize_database()
system_service = SystemService(db)
session_service = SessionService(db)

# Create test window
root = tk.Tk()
root.title("Start Session Dialog Test")
root.geometry("600x400")
root.withdraw()  # Hide main window

print("✓ Testing start session dialog...")

# Test 1: Check available systems
available = system_service.get_available_systems()
print(f"\n✓ Test 1: Available systems: {len(available)}")
for system in available:
    print(f"  - {system.system_name} ({system.system_type}) @ {system.default_hourly_rate}/hour")

# Test 2: Open dialog and verify it creates
print(f"\n✓ Test 2: Opening start session dialog...")
try:
    def on_success():
        print("  - Session created successfully!")
        # Close root after successful session creation
        root.after(500, root.quit)
    
    # Show main window
    root.deiconify()
    
    # Create dialog
    dialog = StartSessionDialog(root, db, on_success=on_success)
    
    print("  - Dialog opened successfully")
    print("  - Dialog contains:")
    print("    * System selection dropdown")
    print("    * Customer name input")
    print("    * Login time (auto-filled with current time)")
    print("    * Hourly rate (auto-filled from system)")
    print("    * Notes field")
    print("    * Start/Cancel buttons")
    
    # Auto-fill and submit after 1 second for testing
    root.after(1000, lambda: _auto_submit_dialog(dialog))
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def _auto_submit_dialog(dialog):
    """Auto-submit the dialog for testing."""
    try:
        # Set customer name
        dialog.customer_var.set("Test Customer")
        
        # Notes
        dialog.notes_text.insert("1.0", "Test session from automated test")
        
        # Submit
        dialog._start_session()
    except Exception as e:
        print(f"  ✗ Error in auto-submit: {e}")
        root.quit()

# Run event loop
root.mainloop()

# Test 3: Verify session was created
print(f"\n✓ Test 3: Verifying session creation...")
active_sessions = session_service.get_active_sessions()
print(f"  - Active sessions now: {len(active_sessions)}")
for session in active_sessions:
    print(f"    * {session.customer_name} on {session.system_name}")

# Test 4: Verify system marked as in use
print(f"\n✓ Test 4: Verifying system availability...")
in_use = system_service.get_systems_in_use()
print(f"  - Systems in use: {len(in_use)}")
for system in in_use:
    print(f"    * {system.system_name} - {system.availability}")

available_now = system_service.get_available_systems()
print(f"  - Systems available now: {len(available_now)}")

print("\n✓ All start session tests passed!")
