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
    """Represents a gaming session."""
    id: int
    date: str
    customer_name: str
    system_id: int
    system_name: str
    login_time: str
    logout_time: Optional[str]
    duration_minutes: Optional[int]
    hourly_rate: float
    extra_charges: float
    total_due: Optional[float]
    payment_status: str
    notes: Optional[str]
    
    def is_active(self) -> bool:
        """Check if session is currently active (no logout time)."""
        return self.logout_time is None


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
        Create a new gaming session.
        
        Args:
            date: Session date (YYYY-MM-DD)
            customer_name: Customer name
            system_id: ID of the gaming system
            login_time: Login time (HH:MM:SS)
            hourly_rate: Hourly rate for this session
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
        
        # Validate login time format
        if not login_time or not isinstance(login_time, str):
            raise SessionError("Invalid login time format.")
        
        try:
            # Validate time format (HH:MM:SS)
            datetime.strptime(login_time, "%H:%M:%S")
        except ValueError:
            raise SessionError(f"Invalid login time format. Expected HH:MM:SS, got: {login_time}")
        
        # Validate hourly rate
        if not isinstance(hourly_rate, (int, float)) or hourly_rate <= 0:
            raise SessionError(f"Invalid hourly rate: {hourly_rate}. Rate must be greater than 0.")
        
        if hourly_rate > 10000:
            raise SessionError("Hourly rate seems unusually high. Please verify.")
        
        # Validate notes length if provided
        if notes and len(notes) > 500:
            raise SessionError("Notes exceed maximum length (500 characters).")
        
        try:
            return self.db.insert(
                """INSERT INTO sessions 
                   (date, customer_name, system_id, login_time, hourly_rate, notes, payment_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (date, customer_name, system_id, login_time, hourly_rate, notes, "Pending")
            )
        except Exception as e:
            raise SessionError(f"Failed to create session in database: {str(e)}")
    
    def end_session(
        self,
        session_id: int,
        logout_time: str,
        extra_charges: float = 0.0,
        payment_status: str = "Pending",
        notes: str = ""
    ) -> bool:
        """
        End a gaming session and calculate totals.
        
        Args:
            session_id: ID of session to end
            logout_time: Logout time (HH:MM:SS)
            extra_charges: Optional extra charges
            payment_status: Payment method ('Paid-Cash', 'Paid-Online', 'Paid-Mixed', or 'Pending')
            notes: Optional notes (booking, payment split, etc.)
        
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
        
        # Validate payment status
        valid_statuses = ["Paid-Cash", "Paid-Online", "Paid-Mixed", "Pending"]
        if payment_status not in valid_statuses:
            raise SessionError(f"Invalid payment status: {payment_status}")
        
        # Validate notes length if provided
        if notes and len(notes) > 500:
            raise SessionError("Notes exceed maximum length (500 characters).")
        
        try:
            # Fetch session to calculate duration
            session = self.get_session_by_id(session_id)
            if not session:
                raise SessionError(f"Session {session_id} not found.")
            
            # Calculate duration in minutes
            login = datetime.strptime(session.login_time, "%H:%M:%S").time()
            logout = datetime.strptime(logout_time, "%H:%M:%S").time()
            
            # Handle overnight sessions (simple case for now)
            login_minutes = login.hour * 60 + login.minute
            logout_minutes = logout.hour * 60 + logout.minute
            
            if logout_minutes < login_minutes:
                # Overnight session
                duration_minutes = (24 * 60 - login_minutes) + logout_minutes
            else:
                duration_minutes = logout_minutes - login_minutes
            
            # Ensure duration is positive
            if duration_minutes <= 0:
                raise SessionError("Logout time must be after login time.")
            
            # Calculate total due
            hours = duration_minutes / 60
            total_due = (session.hourly_rate * hours) + extra_charges
            
            # Update session with payment info
            rows_affected = self.db.update(
                """UPDATE sessions 
                   SET logout_time = ?, duration_minutes = ?, extra_charges = ?, total_due = ?, 
                       payment_status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (logout_time, duration_minutes, extra_charges, total_due, payment_status, notes, session_id)
            )
            return rows_affected > 0
        
        except SessionError:
            raise
        except Exception as e:
            raise SessionError(f"Failed to end session in database: {str(e)}")
    
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
                      s.login_time, s.logout_time, s.duration_minutes, s.hourly_rate,
                      s.extra_charges, s.total_due, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.id = ?""",
            (session_id,)
        )
        return self._row_to_session(row) if row else None
    
    def get_active_sessions(self) -> List[Session]:
        """
        Get all currently active sessions (no logout time).
        
        Returns:
            List of active Session objects
        """
        rows = self.db.fetch_all(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.duration_minutes, s.hourly_rate,
                      s.extra_charges, s.total_due, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.logout_time IS NULL
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
                      s.login_time, s.logout_time, s.duration_minutes, s.hourly_rate,
                      s.extra_charges, s.total_due, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.date = ?
               ORDER BY s.login_time DESC""",
            (date,)
        )
        return [self._row_to_session(row) for row in rows]
    
    def get_pending_sessions(self) -> List[Session]:
        """
        Get all sessions with pending payment.
        
        Returns:
            List of Session objects with payment_status = 'Pending'
        """
        rows = self.db.fetch_all(
            """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                      s.login_time, s.logout_time, s.duration_minutes, s.hourly_rate,
                      s.extra_charges, s.total_due, s.payment_status, s.notes
               FROM sessions s
               JOIN systems sy ON s.system_id = sy.id
               WHERE s.payment_status = 'Pending'
               ORDER BY s.date DESC, s.login_time DESC"""
        )
        return [self._row_to_session(row) for row in rows]
    
    def get_completed_sessions(self, start_date: str = None, end_date: str = None) -> List[Session]:
        """
        Get completed sessions (with logout_time) within optional date range.
        
        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
        
        Returns:
            List of Session objects with logout_time (completed sessions)
        """
        if start_date and end_date:
            rows = self.db.fetch_all(
                """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                          s.login_time, s.logout_time, s.duration_minutes, s.hourly_rate,
                          s.extra_charges, s.total_due, s.payment_status, s.notes
                   FROM sessions s
                   JOIN systems sy ON s.system_id = sy.id
                   WHERE s.logout_time IS NOT NULL
                   AND s.date >= ? AND s.date <= ?
                   ORDER BY s.date DESC, s.login_time DESC""",
                (start_date, end_date)
            )
        elif start_date:
            rows = self.db.fetch_all(
                """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                          s.login_time, s.logout_time, s.duration_minutes, s.hourly_rate,
                          s.extra_charges, s.total_due, s.payment_status, s.notes
                   FROM sessions s
                   JOIN systems sy ON s.system_id = sy.id
                   WHERE s.logout_time IS NOT NULL
                   AND s.date >= ?
                   ORDER BY s.date DESC, s.login_time DESC""",
                (start_date,)
            )
        else:
            rows = self.db.fetch_all(
                """SELECT s.id, s.date, s.customer_name, s.system_id, sy.system_name,
                          s.login_time, s.logout_time, s.duration_minutes, s.hourly_rate,
                          s.extra_charges, s.total_due, s.payment_status, s.notes
                   FROM sessions s
                   JOIN systems sy ON s.system_id = sy.id
                   WHERE s.logout_time IS NOT NULL
                   ORDER BY s.date DESC, s.login_time DESC"""
            )
        return [self._row_to_session(row) for row in rows]
    
    def get_daily_revenue(self, date: str) -> dict:
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
            duration_minutes=row["duration_minutes"],
            hourly_rate=row["hourly_rate"],
            extra_charges=row["extra_charges"],
            total_due=row["total_due"],
            payment_status=row["payment_status"],
            notes=row["notes"],
        )
