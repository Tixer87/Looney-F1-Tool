"""
Dual-Source Aggregation System
Combines Jolpica and FastF1 data for maximum robustness
"""

from typing import Optional, Dict, Any
try:
    from api.providers import jolpica_provider as JP  # type: ignore
    from api.providers import fastf1_provider as FF1  # type: ignore
except Exception:  # pragma: no cover
    from . import jolpica_provider as JP  # type: ignore
    from . import fastf1_provider as FF1  # type: ignore

Driver = Dict[str, Any]
Payload = Dict[str, Any]

def _key(d: Driver) -> str:
    """Generate unique key for driver identification"""
    return str(d.get("DriverNumber") or d.get("Abbreviation") or "").upper()

def _merge_payloads(primary: Payload, secondary: Payload) -> Payload:
    """
    Merge two payloads - primary (Jolpica) provides structure,
    secondary (FastF1) fills gaps
    """
    # Primary (Jolpica) keeps base structure
    result = primary.copy()
    
    # Get drivers list (handle both 'drivers' and 'Drivers' field names)
    p_drivers = list(result.get("drivers") or result.get("Drivers") or [])
    s_drivers = list(secondary.get("drivers") or secondary.get("Drivers") or [])
    
    # Index primary drivers by key
    driver_index = {_key(d): d for d in p_drivers}
    
    # Merge secondary data
    for s_driver in s_drivers:
        key = _key(s_driver)
        if not key:
            continue
            
        target_driver = driver_index.get(key)
        if not target_driver:
            # New driver from secondary source
            p_drivers.append(s_driver)
            driver_index[key] = s_driver
            continue
        
        # Fill empty fields from secondary source
        fill_fields = [
            "Q1", "Q2", "Q3", "FastestLapTime", 
            "GridPosition", "Status", "Position",
            "Points", "Time", "Gap"
        ]
        
        for field in fill_fields:
            if (not target_driver.get(field)) and s_driver.get(field) not in (None, "", "NaT", "0:00:00"):
                target_driver[field] = s_driver[field]
    
    # Normalize field name (handle both cases)
    if "drivers" in result:
        result["drivers"] = p_drivers
    else:
        result["Drivers"] = p_drivers
    
    # Mark as dual-source
    result["source"] = "jolpica+fastf1"
    result["merge_timestamp"] = None  # Could add datetime.now().isoformat()
    
    return result

def _normalize_for_provider(session: str) -> str:
    """Map extended session codes to provider-supported base codes (P/Q/SQ/R)."""
    if session in ("FP1", "FP2", "FP3"):
        return "P"  # practice umbrella
    if session in ("Q1", "Q2", "Q3"):
        return "Q"
    if session in ("SS", "S", "SR"):
        return "SQ"  # treat sprint variants via router/provider candidates
    # Already a base code
    return session if session in ("P", "Q", "SQ", "R") else "R"

def build_dual_payload(season: int, round_no: int, session: str) -> Optional[Payload]:
    """
    Build payload from both sources with intelligent fallback
    Returns merged data if both sources available, single source otherwise
    """
    jolpica_payload: Optional[Payload] = None
    fastf1_payload: Optional[Payload] = None
    
    base_session: str = _normalize_for_provider(session)

    # Try Jolpica first
    try:
        jolpica_payload = JP.export_payload(season, round_no, base_session)
    except Exception:
        # Jolpica failed - log but continue
        jolpica_payload = None
    
    # Try FastF1 second
    try:
        fastf1_payload = FF1.export_payload(season, round_no, base_session)
    except Exception:
        # FastF1 failed - log but continue
        fastf1_payload = None
    
    # Return merged result or single source
    if jolpica_payload and fastf1_payload:
        return _merge_payloads(jolpica_payload, fastf1_payload)
    elif jolpica_payload:
        jolpica_payload["source"] = "jolpica_only"
        return jolpica_payload
    elif fastf1_payload:
        fastf1_payload["source"] = "fastf1_only"
        return fastf1_payload
    else:
        # Both sources failed
        return None

def get_source_status(season: int, round_no: int, session: str) -> Dict[str, Any]:
    """
    Diagnostic function to check which sources are available
    """
    status = {
        "jolpica_available": False,
        "fastf1_available": False,
        "jolpica_error": None,
        "fastf1_error": None
    }
    
    # Test Jolpica
    try:
        result = JP.export_payload(season, round_no, session)
        status["jolpica_available"] = bool(result)
    except Exception as e:
        status["jolpica_error"] = str(e)
    
    # Test FastF1
    try:
        result = FF1.export_payload(season, round_no, session)
        status["fastf1_available"] = bool(result)
    except Exception as e:
        status["fastf1_error"] = str(e)
    
    return status