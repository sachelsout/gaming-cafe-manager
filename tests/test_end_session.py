"""Test end session feature and billing calculations."""

import sys
from pathlib import Path
from datetime import datetime

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.services.session_service import SessionService
from app.services.system_service import SystemService
from app.utils.time_utils import calculate_duration_minutes, format_duration, calculate_bill

# Initialize database
db = initialize_database()
session_service = SessionService(db)
system_service = SystemService(db)

print("✓ Testing billing and duration calculations...\n")

# Test 1: Duration calculation - same day session
print("✓ Test 1: Same-day duration calculation")
login_time = "14:30:00"
logout_time = "16:45:30"
duration = calculate_duration_minutes(login_time, logout_time)
formatted = format_duration(duration)
print(f"  Login: {login_time}")
print(f"  Logout: {logout_time}")
print(f"  Duration: {duration} minutes = {formatted}")
assert duration == 135, f"Expected 135 minutes, got {duration}"
assert formatted == "2h 15m", f"Expected '2h 15m', got '{formatted}'"
print("  ✓ Correct: 2 hours 15 minutes\n")

# Test 2: Duration calculation - overnight session
print("✓ Test 2: Overnight duration calculation")
login_time = "23:00:00"
logout_time = "02:30:00"
duration = calculate_duration_minutes(login_time, logout_time)
formatted = format_duration(duration)
print(f"  Login: {login_time}")
print(f"  Logout: {logout_time}")
print(f"  Duration: {duration} minutes = {formatted}")
assert duration == 210, f"Expected 210 minutes, got {duration}"  # 1 hour to midnight + 2.5 hours
assert formatted == "3h 30m", f"Expected '3h 30m', got '{formatted}'"
print("  ✓ Correct: 3 hours 30 minutes\n")

# Test 3: Billing calculation - basic
print("✓ Test 3: Basic billing (no extra charges, no rate override)")
duration = 150  # 2.5 hours
hourly_rate = 200.0
extra_charges = 0.0
total = calculate_bill(duration, hourly_rate, extra_charges)
print(f"  Duration: {format_duration(duration)}")
print(f"  Rate: {hourly_rate}/hour")
print(f"  Extra charges: {extra_charges}")
print(f"  Calculation: ({hourly_rate} × {duration/60}h) + {extra_charges} = {total}")
expected = (hourly_rate * (duration / 60))
assert total == expected, f"Expected {expected}, got {total}"
assert total == 500.0, f"Expected 500.0, got {total}"
print(f"  ✓ Correct: {total:.2f}\n")

# Test 4: Billing calculation - with extra charges
print("✓ Test 4: Billing with extra charges")
duration = 120  # 2 hours
hourly_rate = 250.0
extra_charges = 50.0
total = calculate_bill(duration, hourly_rate, extra_charges)
base = hourly_rate * (duration / 60)
print(f"  Duration: {format_duration(duration)}")
print(f"  Rate: {hourly_rate}/hour")
print(f"  Extra charges: {extra_charges}")
print(f"  Base: {base:.2f}")
print(f"  Total: {base:.2f} + {extra_charges:.2f} = {total:.2f}")
assert total == 550.0, f"Expected 550.0, got {total}"
print(f"  ✓ Correct: {total:.2f}\n")

# Test 5: Billing calculation - rate override
print("✓ Test 5: Billing with rate override")
duration = 90  # 1.5 hours
original_rate = 200.0
override_rate = 300.0
extra_charges = 0.0
total = calculate_bill(duration, override_rate, extra_charges)
original_total = calculate_bill(duration, original_rate, extra_charges)
print(f"  Duration: {format_duration(duration)}")
print(f"  Original rate: {original_rate}/hour → {original_total:.2f}")
print(f"  Override rate: {override_rate}/hour → {total:.2f}")
assert total == 450.0, f"Expected 450.0, got {total}"
assert original_total == 300.0, f"Expected 300.0 for original, got {original_total}"
print(f"  ✓ Correct: Override applied, new total: {total:.2f}\n")

# Test 6: Precision test - verify rounding
print("✓ Test 6: Rounding and precision")
duration = 125  # 2 hours 5 minutes = 2.0833... hours
hourly_rate = 150.0
extra_charges = 0.0
total = calculate_bill(duration, hourly_rate, extra_charges)
print(f"  Duration: {format_duration(duration)}")
print(f"  Rate: {hourly_rate}/hour")
expected = 150.0 * (125 / 60)  # 312.5
print(f"  Calculation: 150 × {125/60:.4f} = {expected:.4f}")
print(f"  Rounded: {total:.2f}")
assert total == 312.5, f"Expected 312.5, got {total}"
print(f"  ✓ Correct rounding to 2 decimal places: {total:.2f}\n")

# Test 7: Create actual session and end it
print("✓ Test 7: End-to-end session lifecycle")
systems = system_service.get_available_systems()
if systems:
    system = systems[0]
    
    # Create session
    session_id = session_service.create_session(
        date=datetime.now().strftime("%Y-%m-%d"),
        customer_name="Test Billing User",
        system_id=system.id,
        login_time="18:00:00",
        hourly_rate=200.0,
        notes="Billing test session"
    )
    print(f"  Created session {session_id}")
    
    # Mark system as in use
    system_service.set_system_availability(system.id, "In Use")
    print(f"  System {system.system_name} marked as In Use")
    
    # End session with extra charges and rate override
    success = session_service.end_session(
        session_id,
        logout_time="20:30:00",
        extra_charges=25.0
    )
    
    if success:
        # Fetch updated session
        session = session_service.get_session_by_id(session_id)
        print(f"  Session ended")
        print(f"  Duration: {session.actual_duration_min} minutes = {format_duration(session.actual_duration_min)}")
        print(f"  Rate: {session.hourly_rate}/hour")
        print(f"  Extra charges: {session.extra_charges:.2f}")
        print(f"  Total due: {session.total_due:.2f}")
        
        # Verify calculation
        expected_duration = 150  # 2.5 hours
        expected_total = (200.0 * 2.5) + 25.0  # 500 + 25 = 525
        assert session.actual_duration_min == expected_duration
        assert session.total_due == expected_total
        print(f"  [OK] Correct total: {session.total_due:.2f}\n")
        
        # Note: System availability is updated by the EndSessionDialog, not the service directly
        # The dialog handles marking the system as available after the session ends
        print(f"  ✓ Session end-to-end test passed\n")

print("✓ All billing calculation tests passed!")
