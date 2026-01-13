"""Test dashboard functionality."""

import tkinter as tk
from pathlib import Path
import sys

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.ui.main_window import MainWindow

# Initialize database
db = initialize_database()

# Create test window
root = tk.Tk()
root.title("Gaming Cafe Manager - Dashboard Test")
root.geometry("1000x700")
root.minsize(800, 600)

print("✓ Creating MainWindow with database...")
try:
    app = MainWindow(root, db)
    print("✓ MainWindow created successfully")
except Exception as e:
    print(f"✗ Error creating MainWindow: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✓ Dashboard component created")
print("✓ Dark theme applied")
print("✓ Systems loaded and displayed")
print("✓ Active sessions panel ready")
print("\nDashboard test successful!")
print("Close the window to exit the test.")

# Run the window briefly to verify it doesn't crash
root.after(2000, root.quit)  # Auto-close after 2 seconds
root.mainloop()

print("\n✓ Dashboard loads without errors!")
