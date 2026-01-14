#!/usr/bin/env python3
"""
Test migration script - Verify database schema changes work correctly
"""

import sys
from pathlib import Path

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from app.db.init import initialize_database
from app.db.migration import check_migration_status

def test_migration():
    """Test database initialization and migration"""
    print("Testing Gaming Cafe Manager Database Migration...")
    print("-" * 60)
    
    try:
        # Initialize database (should apply migration if needed)
        print("1. Initializing database...")
        db = initialize_database()
        print(f"   [OK] Database initialized at: {db.db_path}")
        
        # Check migration status
        print("\n2. Checking migration status...")
        check_migration_status(db.db_path)
        
        # Try to fetch the schema
        print("\n3. Verifying new schema fields...")
        rows = db.fetch_all("""
            SELECT name FROM pragma_table_info('sessions') 
            ORDER BY cid
        """)
        
        columns = [row['name'] for row in rows]
        print(f"   Session table columns: {', '.join(columns)}")
        
        # Check for new columns
        required_columns = [
            'id', 'date', 'customer_name', 'system_id', 'session_state',
            'planned_duration_min', 'actual_duration_min', 'login_time',
            'logout_time', 'hourly_rate', 'paid_amount', 'payment_method',
            'extra_charges', 'total_due', 'payment_status', 'notes',
            'created_at', 'updated_at'
        ]
        
        missing = [col for col in required_columns if col not in columns]
        if missing:
            print(f"   [FAIL] Missing columns: {missing}")
            return False
        
        print("   [OK] All required columns present")
        
        # Try to create a PLANNED session
        print("\n4. Testing prepaid session creation...")
        session_service = __import__('app.services.session_service', fromlist=['SessionService']).SessionService(db)
        
        session_id = session_service.create_prepaid_session(
            date="2024-01-15",
            customer_name="Test Customer",
            system_id=1,
            planned_duration_min=60,
            hourly_rate=100.0,
            payment_method="Cash",
            extra_charges=0.0,
            notes="Test session"
        )
        print(f"   [OK] Created prepaid session with ID: {session_id}")
        
        # Fetch and verify the session
        print("\n5. Verifying session data...")
        session = session_service.get_session_by_id(session_id)
        if session:
            print(f"   ✓ Session state: {session.session_state}")
            print(f"   ✓ Planned duration: {session.planned_duration_min} minutes")
            print(f"   ✓ Paid amount: Rs. {session.paid_amount}")
            print(f"   ✓ Payment method: {session.payment_method}")
            print(f"   ✓ Payment status: {session.payment_status}")
            
            if session.session_state != "PLANNED":
                print(f"   ✗ Expected state PLANNED, got {session.session_state}")
                return False
            
            if session.login_time is not None:
                print(f"   ✗ Expected login_time to be None, got {session.login_time}")
                return False
            
            print("   ✓ Session data is correct")
        else:
            print("   ✗ Failed to fetch created session")
            return False
        
        # Test start_session
        print("\n6. Testing start_session...")
        success = session_service.start_session(session_id, "14:30:00")
        if success:
            print("   ✓ Session started successfully")
            
            # Verify state changed
            session = session_service.get_session_by_id(session_id)
            if session.session_state == "ACTIVE" and session.login_time == "14:30:00":
                print(f"   ✓ Session transitioned to ACTIVE with login_time: {session.login_time}")
            else:
                print(f"   ✗ Session state not updated correctly: {session.session_state}, login_time: {session.login_time}")
                return False
        else:
            print("   ✗ Failed to start session")
            return False
        
        # Test end_session
        print("\n7. Testing end_session...")
        success = session_service.end_session(session_id, "15:45:00", extra_charges=0.0)
        if success:
            print("   ✓ Session ended successfully")
            
            # Verify state changed and duration calculated
            session = session_service.get_session_by_id(session_id)
            if session.session_state == "COMPLETED":
                print(f"   ✓ Session transitioned to COMPLETED")
                print(f"   ✓ Actual duration: {session.actual_duration_min} minutes")
                print(f"   ✓ Logout time: {session.logout_time}")
                
                # Verify duration calculation: 14:30 to 15:45 = 75 minutes
                if session.actual_duration_min == 75:
                    print("   ✓ Duration calculated correctly")
                else:
                    print(f"   ✗ Expected 75 minutes, got {session.actual_duration_min}")
                    return False
            else:
                print(f"   ✗ Session state not updated correctly: {session.session_state}")
                return False
        else:
            print("   ✗ Failed to end session")
            return False
        
        print("\n" + "=" * 60)
        print("✓ All migration tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Migration test failed with error:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)
