"""Session management service for gaming cafe sessions."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, time
from app.db.connection import DatabaseConnection


class SessionError(Exception):
    """Custom exception for session-related errors."""
    pass


@dataclass
class Session:
    """Represents a gaming session with prepaid-first workflow."""
    id: int
    date: str
    customer_name: str
    system_id: int
    system_name: str
    session_state: str  # PLANNED, ACTIVE, or COMPLETED
    planned_duration_min: int
    login_time: Optional[str]  # None until ACTIVE
    logout_time: Optional[str]  # None until COMPLETED
    actual_duration_min: Optional[int]  # Calculated when COMPLETED
    hourly_rate: float
    paid_amount: float  # Amount paid upfront
    extra_charges: float
    total_due: float  # Total including extras
    payment_method: str  # Cash, Online, Mixed
    payment_status: str  # PAID, Pending, Refunded
    notes: Optional[str]
    
    def is_planned(self) -> bool:
        """Check if session is in PLANNED state (not started yet)."""
        return self.session_state == "PLANNED"
    
    def is_active(self) -> bool:
        """Check if session is currently active (started but not ended)."""
        return self.session_state == "ACTIVE"
    
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.session_state == "COMPLETED"


class SessionService:
    """Service layer for session operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize session service.
        
        Args:
            db: DatabaseConnection instance
        """
        self.db = db
    
    def create_session(
        self,
        date: str,
        customer_name: str,
        system_id: int,
        login_time: str,
        hourly_rate: float,
        notes: Optional[str] = None
    ) -> int:
        """
        DEPRECATED: Compatibility wrapper for old session creation.
        
        This method creates a PLANNED session and immediately starts it (transitions to ACTIVE).
        Use create_prepaid_session() followed by start_session() for better control.
        
        Args:
            date: Session date (YYYY-MM-DD)
            customer_name: Customer name
            system_id: ID of the gaming system
            login_time: Login time (HH:MM:SS) - used as planned start time
            hourly_rate: Hourly rate for this session
            notes: Optional notes
        
        Returns:
            ID of created and started session
        
        Raises:
            SessionError: If validation fails
        """
        # Create a PLANNED session with reasonable defaults
        # Use hourly_rate * 1 hour as default planned duration and payment
        session_id = self.create_prepaid_session(
            date=date,
            customer_name=customer_name,
            system_id=system_id,
            planned_duration_min=60,  # Default 1 hour
            hourly_rate=hourly_rate,
            payment_method="Cash",  # Default to Cash
            extra_charges=0.0,
            notes=notes
        )
        
        # Immediately start the session
        self.start_session(session_id, login_time)
        
        return session_id
    
    def create_prepaid_session(
        self,
        date: str,
        customer_name: str,
        system_id: int,
        planned_duration_min: int,
        hourly_rate: float,
        payment_method: str,
        extra_charges: float = 0.0,
        notes: Optional[str] = None
    ) -> int:
        """
        Create a new prepaid session in PLANNED state.
        
        This is the new prepaid-first workflow:
        1. Create session with planned duration and payment
        2. Start session when customer is ready
        3. End session after customer finishes
        
        Args:
            date: Session date (YYYY-MM-DD)
            customer_name: Customer name
            system_id: ID of the gaming system
            planned_duration_min: Planned duration in minutes
            hourly_rate: Hourly rate for this session
            payment_method: 'Cash', 'Online', or 'Mixed'
            extra_charges: Optional extra charges (added to total)
            notes: Optional notes
        
        Returns:
            ID of created session
        
        Raises:
            SessionError: If validation fails
        """
        # Validate customer name
        if not customer_name or not customer_name.strip():
            raise SessionError("Customer name cannot be empty.")
        
        customer_name = customer_name.strip()
        if len(customer_name) > 100:
            raise SessionError("Customer name exceeds maximum length (100 characters).")
        
        # Validate system ID
        if not isinstance(system_id, int) or system_id <= 0:
            raise SessionError("Invalid system ID.")
        
        # Validate planned duration
        if not isinstance(planned_duration_min, int) or planned_duration_min <= 0:
            raise SessionError("Planned duration must be a positive integer (minutes).")
        
        if planned_duration_min > 1440:  # Max 24 hours
            raise SessionError("Planned duration cannot exceed 24 hours (1440 minutes).")
        
        # Validate hourly rate
        if not isinstance(hourly_rate, (int, float)) or hourly_rate <= 0:
            raise SessionError(f"Invalid hourly rate: {hourly_rate}. Rate must be greater than 0.")
        
        if hourly_rate > 10000:
            raise SessionError("Hourly rate seems unusually high. Please verify.")
        
        # Validate payment method
        valid_methods = ["Cash", "Online", "Mixed"]
        if payment_method not in valid_methods:
            raise SessionError(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        
        # Validate extra charges
        if not isinstance(extra_charges, (int, float)) or extra_charges < 0:
            raise SessionError("Extra charges must be non-negative.")
        
        # Validate notes length if provided
        if notes and len(notes) > 500:
            raise SessionError("Notes exceed maximum length (500 characters).")
        
        try:
            # Calculate paid amount (hourly_rate * (duration_min / 60) + extra_charges)
            hours = planned_duration_min / 60.0
            paid_amount = (hourly_rate * hours) + extra_charges
            
            return self.db.insert(
                """INSERT INTO sessions 
                   (date, customer_name, system_id, session_state, planned_duration_min, 
                    hourly_rate, paid_amount, extra_charges, total_due, payment_method, 
                    payment_status, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (date, customer_name, system_id, "PLANNED", planned_duration_min,
                 hourly_rate, paid_amount, extra_charges, paid_amount, payment_method,
                 "PAID", notes)
            )
        except Exception as e:
            raise SessionError(f"Failed to create prepaid session: {str(e)}")
    
    def start_session(self, session_id: int, login_time: str) -> bool:
        """
        Start a PLANNED session (transition to ACTIVE).
        
        Records the login_time when customer begins playing.
        
        Args:
            session_id: ID of session to start
            login_time: Login time (HH:MM:SS)
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            SessionError: If validation fails
        """
        # Validate session ID
        if not isinstance(session_id, int) or session_id <= 0:
            raise SessionError("Invalid session ID.")
        
        # Validate login time format
        if not login_time or not isinstance(login_time, str):
            raise SessionError("Invalid login time format.")
        
        try:
            datetime.strptime(login_time, "%H:%M:%S")
        except ValueError:
            raise SessionError(f"Invalid login time format. Expected HH:MM:SS, got: {login_time}")
        
        try:
            # Fetch session
            session = self.get_session_by_id(session_id)
            if not session:
                raise SessionError(f"Session {session_id} not found.")
            
            if session.session_state != "PLANNED":
                raise SessionError(f"Can only start PLANNED sessions. Current state: {session.session_state}")
            
            # Update session: set to ACTIVE and record login_time
            rows_affected = self.db.update(
                """UPDATE sessions 
                   SET session_state = 'ACTIVE', login_time = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (login_time, session_id)
            )
            return rows_affected > 0
        
        except SessionError:
            raise
        except Exception as e:
            raise SessionError(f"Failed to start session: {str(e)}")
    
    def end_session(
        self,
        session_id: int,
        logout_time: str,
        extra_charges: float = 0.0,
        notes: str = ""
    ) -> bool:
        """
        End an ACTIVE session (transition to COMPLETED).
        
        In the prepaid model, payment is already recorded. This method:
        - Records logout_time
        - Calculates actual_duration_min
        - Compares actual vs planned duration (for future refund/extra charge handling)
        - Marks session as COMPLETED
        
        Args:
            session_id: ID of session to end
            logout_time: Logout time (HH:MM:SS)
            extra_charges: Optional additional charges (default 0)
            notes: Optional notes
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            SessionError: If validation fails
        """
        # Validate session ID
        if not isinstance(session_id, int) or session_id <= 0:
            raise SessionError("Invalid session ID.")
        
        # Validate logout time format
        if not logout_time or not isinstance(logout_time, str):
            raise SessionError("Invalid logout time format.")
        
        try:
            # Validate time format (HH:MM:SS)
            datetime.strptime(logout_time, "%H:%M:%S")
        except ValueError:
            raise SessionError(f"Invalid logout time format. Expected HH:MM:SS, got: {logout_time}")
        
        # Validate extra charges
        if not isinstance(extra_charges, (int, float)) or extra_charges < 0:
            raise SessionError(f"Invalid extra charges: {extra_charges}. Must be >= 0.")
        
        if extra_charges > 100000:
            raise SessionError("Extra charges amount seems unusually high. Please verify.")
        
        # Validate notes length if provided
        if notes and len(notes) > 500:
            raise SessionError("Notes exceed maximum length (500 characters).")
        
        try:
            # Fetch session
            session = self.get_session_by_id(session_id)
            if not session:
                raise SessionError(f"Session {session_id} not found.")
            
            # Verify session is in ACTIVE state
            if session.session_state != "ACTIVE":
                raise SessionError(f"Can only end ACTIVE sessions. Current state: {session.session_state}")
            
            # Verify login_time exists
            if not session.login_time:
                raise SessionError(f"Session {session_id} has no login time recorded.")
            
            # Calculate actual duration in minutes
            login = datetime.strptime(session.login_time, "%H:%M:%S").time()
            logout = datetime.strptime(logout_time, "%H:%M:%S").time()
            
            # Handle overnight sessions
            login_minutes = login.hour * 60 + login.minute
            logout_minutes = logout.hour * 60 + logout.minute
            
            if logout_minutes < login_minutes:
                # Overnight session
                actual_duration_min = (24 * 60 - login_minutes) + logout_minutes
            else:
                actual_duration_min = logout_minutes - login_minutes
            
            # Ensure duration is positive
            if actual_duration_min <= 0:
                raise SessionError("Logout time must be after login time.")
            
            # Calculate new total_due if there are extra charges
            new_total_due = session.paid_amount + extra_charges
            
            # Update session: transition to COMPLETED, record logout_time and actual duration
            rows_affected = self.db.update(
                """UPDATE sessions 
                   SET session_state = 'COMPLETED', logout_time = ?, actual_duration_min = ?, 
                       extra_charges = ?, total_due = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (logout_time, actual_duration_min, extra_charges, new_total_due, notes, session_id)
            )
            return rows_affected > 0
        
        except SessionError:
            raise
        except Exception as e:
            raise SessionError(f"Failed to end session: {str(e)}")
    
    def get_session_by_id(self, session_id: int) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            Session object or None if not found
        """
        row = self.db.fetch_one(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                      s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                      s.paid_amount, s.payment_method, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.id = ?""",
            (session_id,)
        )
        return self._row_to_session(row) if row else None
        return self._row_to_session(row) if row else None
    
    def get_active_sessions(self) -> List[Session]:
        """
        Get all currently active sessions (ACTIVE state).
        
        Returns:
            List of active Session objects
        """
        rows = self.db.fetch_all(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                      s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                      s.paid_amount, s.payment_method, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.session_state = 'ACTIVE'
               ORDER BY s.login_time DESC"""
        )
        return [self._row_to_session(row) for row in rows]
    
    def get_sessions_by_date(self, date: str) -> List[Session]:
        """
        Get all sessions for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            List of Session objects
        """
        rows = self.db.fetch_all(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                      s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                      s.paid_amount, s.payment_method, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.date = ?
               ORDER BY s.login_time DESC""",
            (date,)
        )
        return [self._row_to_session(row) for row in rows]
    
    def get_pending_sessions(self) -> List[Session]:
        """
        Get all sessions with pending payment (payment_status = 'Pending').
        
        Returns:
            List of Session objects with payment_status = 'Pending'
        """
        rows = self.db.fetch_all(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                      s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                      s.paid_amount, s.payment_method, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.payment_status = 'Pending'
               ORDER BY s.date DESC, s.login_time DESC"""
        )
        return [self._row_to_session(row) for row in rows]
    
    def get_completed_sessions(self, start_date: str = None, end_date: str = None) -> List[Session]:
        """
        Get completed sessions (session_state = 'COMPLETED') within optional date range.
        
        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
        
        Returns:
            List of Session objects with session_state = 'COMPLETED'
        """
        if start_date and end_date:
            rows = self.db.fetch_all(
                """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                          s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                          s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                          s.paid_amount, s.payment_method, s.payment_status, s.notes
                   FROM sessions s
                   JOIN systems sy ON s.system_id = sy.id
                   WHERE s.session_state = 'COMPLETED'
                   AND s.date >= ? AND s.date <= ?
                   ORDER BY s.date DESC, s.login_time DESC""",
                (start_date, end_date)
            )
        elif start_date:
            rows = self.db.fetch_all(
                """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                          s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                          s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                          s.paid_amount, s.payment_method, s.payment_status, s.notes
                   FROM sessions s
                   JOIN systems sy ON s.system_id = sy.id
                   WHERE s.session_state = 'COMPLETED'
                   AND s.date >= ?
                   ORDER BY s.date DESC, s.login_time DESC""",
                (start_date,)
            )
        else:
            rows = self.db.fetch_all(
                """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                          s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                          s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                          s.paid_amount, s.payment_method, s.payment_status, s.notes
                   FROM sessions s
                   JOIN systems sy ON s.system_id = sy.id
                   WHERE s.session_state = 'COMPLETED'
                   ORDER BY s.date DESC, s.login_time DESC"""
            )
        return [self._row_to_session(row) for row in rows]
    
    def get_planned_sessions(self) -> List[Session]:
        """
        Get all PLANNED sessions (not yet started).
        
        Returns:
            List of Session objects with session_state = 'PLANNED'
        """
        rows = self.db.fetch_all(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                      s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                      s.paid_amount, s.payment_method, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.session_state = 'PLANNED'
               ORDER BY s.date DESC, s.id DESC"""
        )
        return [self._row_to_session(row) for row in rows]
    
    def get_sessions_by_state(self, state: str) -> List[Session]:
        """
        Get all sessions in a specific state.
        
        Args:
            state: 'PLANNED', 'ACTIVE', or 'COMPLETED'
        
        Returns:
            List of Session objects in the specified state
        
        Raises:
            ValueError: If state is invalid
        """
        valid_states = ("PLANNED", "ACTIVE", "COMPLETED")
        if state not in valid_states:
            raise ValueError(f"Invalid session state: {state}")
        
        rows = self.db.fetch_all(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.session_state, s.planned_duration_min,
                      s.actual_duration_min, s.hourly_rate, s.extra_charges, s.total_due, 
                      s.paid_amount, s.payment_method, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.session_state = ?
               ORDER BY s.date DESC, s.login_time DESC""",
            (state,)
        )
        return [self._row_to_session(row) for row in rows]
        """
        Calculate daily revenue summary for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            Dictionary with:
            - total_revenue: Total amount collected for the day
            - session_count: Number of sessions completed
            - cash_total: Total from cash payments
            - online_total: Total from online payments
            - mixed_total: Total from mixed payments
            - pending_total: Total from pending payments
        """
        rows = self.db.fetch_all(
            """SELECT COALESCE(SUM(CASE WHEN payment_status = 'Paid-Cash' THEN total_due ELSE 0 END), 0) as cash_total,
                      COALESCE(SUM(CASE WHEN payment_status = 'Paid-Online' THEN total_due ELSE 0 END), 0) as online_total,
                      COALESCE(SUM(CASE WHEN payment_status = 'Paid-Mixed' THEN total_due ELSE 0 END), 0) as mixed_total,
                      COALESCE(SUM(CASE WHEN payment_status = 'Pending' THEN total_due ELSE 0 END), 0) as pending_total,
                      COUNT(*) as session_count,
                      COALESCE(SUM(CASE WHEN payment_status IN ('Paid-Cash', 'Paid-Online', 'Paid-Mixed') THEN total_due ELSE 0 END), 0) as total_revenue
               FROM sessions
               WHERE date = ? AND logout_time IS NOT NULL""",
            (date,)
        )
        
        if rows and rows[0]:
            row = rows[0]
            return {
                'total_revenue': row['total_revenue'] or 0.0,
                'session_count': row['session_count'] or 0,
                'cash_total': row['cash_total'] or 0.0,
                'online_total': row['online_total'] or 0.0,
                'mixed_total': row['mixed_total'] or 0.0,
                'pending_total': row['pending_total'] or 0.0
            }
        return {
            'total_revenue': 0.0,
            'session_count': 0,
            'cash_total': 0.0,
            'online_total': 0.0,
            'mixed_total': 0.0,
            'pending_total': 0.0
        }
    
    def get_date_range_revenue(self, start_date: str, end_date: str) -> dict:
        """
        Calculate revenue summary for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with revenue breakdown by payment method and totals
        """
        rows = self.db.fetch_all(
            """SELECT COALESCE(SUM(CASE WHEN payment_status = 'Paid-Cash' THEN total_due ELSE 0 END), 0) as cash_total,
                      COALESCE(SUM(CASE WHEN payment_status = 'Paid-Online' THEN total_due ELSE 0 END), 0) as online_total,
                      COALESCE(SUM(CASE WHEN payment_status = 'Paid-Mixed' THEN total_due ELSE 0 END), 0) as mixed_total,
                      COALESCE(SUM(CASE WHEN payment_status = 'Pending' THEN total_due ELSE 0 END), 0) as pending_total,
                      COUNT(*) as session_count,
                      COALESCE(SUM(CASE WHEN payment_status IN ('Paid-Cash', 'Paid-Online', 'Paid-Mixed') THEN total_due ELSE 0 END), 0) as total_revenue
               FROM sessions
               WHERE date >= ? AND date <= ? AND logout_time IS NOT NULL""",
            (start_date, end_date)
        )
        
        if rows and rows[0]:
            row = rows[0]
            return {
                'total_revenue': row['total_revenue'] or 0.0,
                'session_count': row['session_count'] or 0,
                'cash_total': row['cash_total'] or 0.0,
                'online_total': row['online_total'] or 0.0,
                'mixed_total': row['mixed_total'] or 0.0,
                'pending_total': row['pending_total'] or 0.0
            }
        return {
            'total_revenue': 0.0,
            'session_count': 0,
            'cash_total': 0.0,
            'online_total': 0.0,
            'mixed_total': 0.0,
            'pending_total': 0.0
        }
    
    def update_payment_status(self, session_id: int, payment_status: str) -> bool:
        """
        Update session payment status.
        
        Args:
            session_id: Session ID
            payment_status: 'Paid-Cash', 'Paid-Online', or 'Pending'
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            ValueError: If payment_status is invalid
        """
        valid_statuses = ("Paid-Cash", "Paid-Online", "Pending")
        if payment_status not in valid_statuses:
            raise ValueError(f"Invalid payment status: {payment_status}")
        
        rows_affected = self.db.update(
            "UPDATE sessions SET payment_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payment_status, session_id)
        )
        return rows_affected > 0
    
    def _row_to_session(self, row) -> Session:
        """Convert database row to Session object."""
        return Session(
            id=row["id"],
            date=row["date"],
            customer_name=row["customer_name"],
            system_id=row["system_id"],
            system_name=row["system_name"],
            login_time=row["login_time"],
            logout_time=row["logout_time"],
            session_state=row["session_state"],
            planned_duration_min=row["planned_duration_min"],
            actual_duration_min=row["actual_duration_min"],
            hourly_rate=row["hourly_rate"],
            extra_charges=row["extra_charges"],
            total_due=row["total_due"],
            paid_amount=row["paid_amount"],
            payment_method=row["payment_method"],
            payment_status=row["payment_status"],
            notes=row["notes"],
        )
