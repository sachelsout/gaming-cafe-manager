"""System management service for gaming cafe systems/consoles."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.db.connection import DatabaseConnection


@dataclass
class System:
    """Represents a gaming system/console."""
    id: int
    system_name: str
    system_type: str
    default_hourly_rate: float
    availability: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system to dictionary."""
        return {
            "id": self.id,
            "system_name": self.system_name,
            "system_type": self.system_type,
            "default_hourly_rate": self.default_hourly_rate,
            "availability": self.availability,
        }


class SystemService:
    """Service layer for system operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize system service.
        
        Args:
            db: DatabaseConnection instance
        """
        self.db = db
    
    def get_all_systems(self) -> List[System]:
        """
        Fetch all systems.
        
        Returns:
            List of System objects
        """
        rows = self.db.fetch_all(
            "SELECT id, system_name, system_type, default_hourly_rate, availability FROM systems ORDER BY system_name"
        )
        return [self._row_to_system(row) for row in rows]
    
    def get_system_by_id(self, system_id: int) -> Optional[System]:
        """
        Get system by ID.
        
        Args:
            system_id: System ID
        
        Returns:
            System object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT id, system_name, system_type, default_hourly_rate, availability FROM systems WHERE id = ?",
            (system_id,)
        )
        return self._row_to_system(row) if row else None
    
    def get_available_systems(self) -> List[System]:
        """
        Fetch only available systems (not in use).
        
        Returns:
            List of available System objects
        """
        rows = self.db.fetch_all(
            "SELECT id, system_name, system_type, default_hourly_rate, availability FROM systems WHERE availability = 'Available' ORDER BY system_name"
        )
        return [self._row_to_system(row) for row in rows]
    
    def get_systems_in_use(self) -> List[System]:
        """
        Fetch systems currently in use.
        
        Returns:
            List of System objects that are in use
        """
        rows = self.db.fetch_all(
            "SELECT id, system_name, system_type, default_hourly_rate, availability FROM systems WHERE availability = 'In Use' ORDER BY system_name"
        )
        return [self._row_to_system(row) for row in rows]
    
    def set_system_availability(self, system_id: int, availability: str) -> bool:
        """
        Update system availability status.
        
        Args:
            system_id: System ID
            availability: 'Available' or 'In Use'
        
        Returns:
            True if update successful, False otherwise
        
        Raises:
            ValueError: If availability is not valid
        """
        if availability not in ("Available", "In Use"):
            raise ValueError(f"Invalid availability: {availability}. Must be 'Available' or 'In Use'")
        
        rows_affected = self.db.update(
            "UPDATE systems SET availability = ? WHERE id = ?",
            (availability, system_id)
        )
        return rows_affected > 0
    
    def get_system_rate(self, system_id: int) -> Optional[float]:
        """
        Get default hourly rate for a system.
        
        Args:
            system_id: System ID
        
        Returns:
            Hourly rate or None if system not found
        """
        system = self.get_system_by_id(system_id)
        return system.default_hourly_rate if system else None
    
    def _row_to_system(self, row) -> System:
        """Convert database row to System object."""
        return System(
            id=row["id"],
            system_name=row["system_name"],
            system_type=row["system_type"],
            default_hourly_rate=row["default_hourly_rate"],
            availability=row["availability"],
        )
