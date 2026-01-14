"""Session timer for monitoring active gaming sessions and triggering notifications."""

import threading
import time
from datetime import datetime
from typing import Callable, Optional, Dict
from dataclasses import dataclass


@dataclass
class SessionTimerState:
    """State information for a session timer."""
    session_id: int
    customer_name: str
    system_name: str
    planned_duration_min: int
    start_time: datetime
    notification_triggered: bool = False
    

class SessionTimer:
    """Monitors active sessions and triggers notifications when time is running out."""
    
    def __init__(
        self,
        session_id: int,
        customer_name: str,
        system_name: str,
        planned_duration_min: int,
        login_time_24hr: str,
        on_warning: Optional[Callable[[str], None]] = None,
        on_time_up: Optional[Callable[[str], None]] = None,
        warning_threshold_min: int = 5
    ):
        """
        Initialize session timer.
        
        Args:
            session_id: ID of the session
            customer_name: Name of customer
            system_name: Name of gaming system
            planned_duration_min: Planned duration in minutes
            login_time_24hr: Session login time in 24-hour format (HH:MM:SS)
            on_warning: Callback when warning threshold is reached (5 min remaining)
            on_time_up: Callback when time is up
            warning_threshold_min: Minutes to warn before time is up (default 5)
        """
        self.session_id = session_id
        self.customer_name = customer_name
        self.system_name = system_name
        self.planned_duration_min = planned_duration_min
        self.on_warning = on_warning
        self.on_time_up = on_time_up
        self.warning_threshold_min = warning_threshold_min
        
        # Parse login time and create start_time from it
        try:
            from app.utils.time_utils import parse_time_24hr_to_datetime
            self.start_time = parse_time_24hr_to_datetime(login_time_24hr)
        except:
            # Fallback: use current time if parsing fails
            self.start_time = datetime.now()
        
        self.is_running = False
        self.timer_thread: Optional[threading.Thread] = None
        self.warning_triggered = False
        self.time_up_triggered = False
        
    def start(self):
        """Start the timer in a background thread."""
        if self.is_running:
            return
        
        self.is_running = True
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()
    
    def stop(self):
        """Stop the timer."""
        self.is_running = False
        if self.timer_thread:
            self.timer_thread.join(timeout=1)
    
    def _run_timer(self):
        """Run timer in background thread."""
        while self.is_running:
            try:
                elapsed_time = (datetime.now() - self.start_time).total_seconds() / 60
                remaining_time = self.planned_duration_min - elapsed_time
                
                # Trigger warning when 5 minutes remaining
                if (remaining_time <= self.warning_threshold_min and 
                    not self.warning_triggered and remaining_time > 0):
                    self.warning_triggered = True
                    if self.on_warning:
                        remaining_sec = int(remaining_time * 60)
                        self.on_warning(
                            f"⏰ WARNING: {self.customer_name} ({self.system_name}) has "
                            f"{remaining_sec // 60}m {remaining_sec % 60}s remaining!"
                        )
                
                # Trigger time up when session exceeds planned duration
                if remaining_time <= 0 and not self.time_up_triggered:
                    self.time_up_triggered = True
                    if self.on_time_up:
                        self.on_time_up(
                            f"⏱️ TIME UP: {self.customer_name} ({self.system_name}) "
                            f"has exceeded their {self.planned_duration_min} minute session!"
                        )
                    self.is_running = False
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error in session timer: {str(e)}")
                self.is_running = False
    
    def get_remaining_time(self) -> int:
        """Get remaining time in minutes."""
        elapsed_time = (datetime.now() - self.start_time).total_seconds() / 60
        remaining = max(0, self.planned_duration_min - elapsed_time)
        return int(remaining)
    
    def get_remaining_time_formatted(self) -> str:
        """Get remaining time as formatted string (HH:MM:SS)."""
        elapsed_time = (datetime.now() - self.start_time).total_seconds() / 60
        remaining_min = max(0, self.planned_duration_min - elapsed_time)
        
        total_remaining_sec = int(remaining_min * 60)
        hours = total_remaining_sec // 3600
        remaining_after_hours = total_remaining_sec % 3600
        minutes = remaining_after_hours // 60
        seconds = remaining_after_hours % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class SessionTimerManager:
    """Manages multiple session timers."""
    
    def __init__(
        self,
        on_warning: Optional[Callable[[str], None]] = None,
        on_time_up: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize timer manager.
        
        Args:
            on_warning: Global callback for warning notifications
            on_time_up: Global callback for time-up notifications
        """
        self.on_warning = on_warning
        self.on_time_up = on_time_up
        self.timers: Dict[int, SessionTimer] = {}
        self._lock = threading.Lock()
    
    def add_session(
        self,
        session_id: int,
        customer_name: str,
        system_name: str,
        planned_duration_min: int,
        login_time_24hr: str
    ) -> SessionTimer:
        """
        Add and start a new session timer.
        
        Args:
            session_id: ID of the session
            customer_name: Name of customer
            system_name: Name of gaming system
            planned_duration_min: Planned duration in minutes
            login_time_24hr: Session login time in 24-hour format (HH:MM:SS)
        
        Returns:
            SessionTimer instance
        """
        with self._lock:
            # Stop any existing timer for this session
            if session_id in self.timers:
                self.timers[session_id].stop()
            
            # Create new timer
            timer = SessionTimer(
                session_id=session_id,
                customer_name=customer_name,
                system_name=system_name,
                planned_duration_min=planned_duration_min,
                login_time_24hr=login_time_24hr,
                on_warning=self.on_warning,
                on_time_up=self.on_time_up
            )
            
            self.timers[session_id] = timer
            timer.start()
            return timer
    
    def remove_session(self, session_id: int):
        """Remove and stop a session timer."""
        with self._lock:
            if session_id in self.timers:
                self.timers[session_id].stop()
                del self.timers[session_id]
    
    def get_timer(self, session_id: int) -> Optional[SessionTimer]:
        """Get a session timer by session ID."""
        with self._lock:
            return self.timers.get(session_id)
    
    def get_all_timers(self) -> Dict[int, SessionTimer]:
        """Get all active timers."""
        with self._lock:
            return self.timers.copy()
    
    def stop_all(self):
        """Stop all timers."""
        with self._lock:
            for timer in self.timers.values():
                timer.stop()
            self.timers.clear()
