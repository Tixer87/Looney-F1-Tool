# api/providers/router.py
from __future__ import annotations
from .jolpica_provider import JolpicaProvider
from . import fastf1_provider as ff1

class FastF1ProviderWrapper:
    """Wrapper für FastF1-Funktionen als Provider-Objekt"""
    name = "fastf1"
    
    def is_available(self) -> bool:
        return True  # FastF1 ist immer verfügbar (Offline-Cache)
    
    def schedule(self, year: int) -> list[dict]:
        return ff1.schedule(year)
    
    def fetch_session_raw(self, year: int, round_no: int, session_type: str) -> dict:
        from .base import SessionType
        # Cast zum korrekten Typ
        session: SessionType = session_type  # type: ignore
        payload = ff1.export_payload(year, round_no, session)
        if not payload:
            return {
                "provider": self.name,
                "year": year,
                "round": round_no,
                "sessionType": session_type,
                "Drivers": [],
            }
        return payload

def get_provider(prefer: str | None = None, year: int | None = None):
    """
    Router für Provider-Auswahl mit Jahr-basierter Strategie.
    
    Strategy:
    - Year >= 2023: FastF1 preferred (more sessions: FP1-3, Q, Sprint, Race)
    - Year < 2023: Jolpica preferred (historical data back to 1950)
    - No year: Jolpica with FastF1 fallback
    
    Args:
        prefer: Force specific provider ("jolpica" or "fastf1")
        year: Season year for auto-selection strategy
        
    Returns:
        Provider instance (JolpicaProvider or FastF1ProviderWrapper)
    """
    if prefer == "fastf1":
        return FastF1ProviderWrapper()
    if prefer == "jolpica":
        p = JolpicaProvider()
        return p if p.is_available() else FastF1ProviderWrapper()

    # Year-based auto-selection
    if year and year >= 2023:
        # Newer seasons: FastF1 preferred (more sessions: FP1-3, Q, Sprint, Race)
        return FastF1ProviderWrapper()
    
    # Older seasons or no year: Jolpica preferred (historical data)
    jp = JolpicaProvider()
    if jp.is_available():
        return jp
    return FastF1ProviderWrapper()

