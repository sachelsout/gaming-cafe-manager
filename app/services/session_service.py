"""Session management service for gaming cafe sessions."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, time
from app.db.connection import DatabaseConnection


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
        """
        return self.db.insert(
            """INSERT INTO sessions 
               (date, customer_name, system_id, login_time, hourly_rate, notes, payment_status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (date, customer_name, system_id, login_time, hourly_rate, notes, "Pending")
        )
    
    def end_session(
        self,
        session_id: int,
        logout_time: str,
        extra_charges: float = 0.0
    ) -> bool:
        """
        End a gaming session and calculate totals.
        
        Args:
            session_id: ID of session to end
            logout_time: Logout time (HH:MM:SS)
            extra_charges: Optional extra charges
        
        Returns:
            True if successful, False otherwise
        """
        # Fetch session to calculate duration
        session = self.get_session_by_id(session_id)
        if not session:
            return False
        
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
        
        # Calculate total due
        hours = duration_minutes / 60
        total_due = (session.hourly_rate * hours) + extra_charges
        
        # Update session
        rows_affected = self.db.update(
            """UPDATE sessions 
               SET logout_time = ?, duration_minutes = ?, extra_charges = ?, total_due = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (logout_time, duration_minutes, extra_charges, total_due, session_id)
        )
        return rows_affected > 0
    
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
