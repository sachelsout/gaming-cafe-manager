"""Test database initialization."""

from app.db.init import initialize_database

# Initialize database
db = initialize_database()

# Check tables
tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
print("✓ Tables created:")
for table in tables:
    print(f"  - {table['name']}")

# Check default systems
systems = db.fetch_all("SELECT * FROM systems")
print(f"\n✓ Default systems inserted ({len(systems)}):")
for system in systems:
    print(f"  - {system['system_name']}")

# Check database file exists
import os
from pathlib import Path
db_path = Path(__file__).parent / "data" / "cafe.db"
if db_path.exists():
    size_kb = db_path.stat().st_size / 1024
    print(f"\n✓ Database file created: {db_path} ({size_kb:.1f} KB)")

print("\n✓ All tests passed!")
