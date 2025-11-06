# api/providers/base.py
from typing import Protocol, Literal, Optional, Dict, Any, List

SessionType = Literal["P", "Q", "SQ", "R"]


# Custom exceptions for provider operations
class ProviderError(Exception):
    """Base exception for all provider errors"""
    pass


class ProviderUnavailable(ProviderError):
    """Raised when a provider is unavailable or unreachable"""
    pass


class ProviderTimeout(ProviderError):
    """Raised when a provider request times out"""
    pass


class ProviderDataError(ProviderError):
    """Raised when provider returns invalid or incomplete data"""
    pass

class DataProvider(Protocol):
    """Protocol for F1 data providers"""
    
    def schedule(self, season: int) -> List[Dict[str, Any]]:
        """Get race schedule for a season
        
        Returns:
            List of race events with round, date, raceName, Circuit, etc.
        """
        ...
    
    def export_payload(self, season: int, round_no: int, session: SessionType) -> Optional[Dict[str, Any]]:
        """Get export data for a specific session
        
        Returns:
            Dictionary with session data ready for export, or None if no data
        """
        ...