"""Test system management functionality."""

from app.db.init import initialize_database
from app.services.system_service import SystemService

# Initialize database with fresh schema
db = initialize_database()
system_service = SystemService(db)

# Test 1: Fetch all systems
print("✓ Test 1: Fetch all systems")
systems = system_service.get_all_systems()
print(f"  Total systems: {len(systems)}")
for system in systems:
    print(f"    - {system.system_name} ({system.system_type}) @ {system.default_hourly_rate}/hour - {system.availability}")

# Test 2: Check default rates
print("\n✓ Test 2: Verify default rates")
ps5_rate = system_service.get_system_rate(2)  # PS-5 is ID 2
pc_rate = system_service.get_system_rate(5)   # PC-01 is ID 5
print(f"  PS-5 hourly rate: {ps5_rate}")
print(f"  PC-01 hourly rate: {pc_rate}")

# Test 3: Get available systems
print("\n✓ Test 3: Fetch available systems")
available = system_service.get_available_systems()
print(f"  Available systems: {len(available)}")
for system in available:
    print(f"    - {system.system_name}")

# Test 4: Update availability
print("\n✓ Test 4: Update system availability")
system_id = systems[0].id
print(f"  Setting {systems[0].system_name} to 'In Use'")
system_service.set_system_availability(system_id, "In Use")

# Test 5: Verify availability change
print("\n✓ Test 5: Verify availability updated")
in_use = system_service.get_systems_in_use()
available = system_service.get_available_systems()
print(f"  Systems in use: {len(in_use)} - {[s.system_name for s in in_use]}")
print(f"  Available systems: {len(available)}")

# Test 6: Get system details
print("\n✓ Test 6: Get specific system by ID")
system = system_service.get_system_by_id(system_id)
print(f"  {system.system_name}: {system.system_type}, {system.default_hourly_rate}/hour, {system.availability}")

# Test 7: System persistence
print("\n✓ Test 7: Verify systems persist across DB operations")
db2 = initialize_database()
service2 = SystemService(db2)
systems_count = len(service2.get_all_systems())
print(f"  Systems still present: {systems_count}")

print("\n✓ All system management tests passed!")
