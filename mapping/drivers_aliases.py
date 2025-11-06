"""Driver resolution with unified alias authority.

Maps driver number/code/name to canonical driver info using:
1. lineups.f1.json (source of truth for 2025 season)
2. driver_alias_map.json (common aliases and shortcuts)
3. drivers.json (full driver details including Nationality)

API:
    get_driver_by_number(number, year) -> dict
    get_driver_by_code(code, year) -> dict
    get_driver_by_name(name, year) -> dict
    get_driver_full_info(name) -> dict  # NEW: includes Nationality from drivers.json
    
All return: {"Name", "Code", "Number", "Nationality", "TeamConstructorId"}
"""

import json
from pathlib import Path
from typing import Optional
from mapping.normalize import normalize_key
from utils.logging_setup import get_logger

log = get_logger(__name__)

# Load data once at module level
LINEUPS_FILE = Path(__file__).parent / "lineups.f1.json"
ALIAS_FILE = Path(__file__).parent / "driver_alias_map.json"
DRIVERS_FILE = Path(__file__).parent / "drivers.json"  # NEW: Full driver details

_lineups_data = {}
_alias_map = {}
_drivers_full = {}  # NEW: Full driver info keyed by normalized name
_loaded = False

# Indexes for fast lookup
_by_number = {}
_by_code = {}
_by_name = {}


def _load_data():
    """Load lineups.f1.json, driver_alias_map.json, and drivers.json."""
    global _lineups_data, _alias_map, _drivers_full, _loaded
    global _by_number, _by_code, _by_name
    
    if _loaded:
        return
    
    # Load lineups.f1.json (flat array with Championship filter)
    try:
        with open(LINEUPS_FILE, 'r', encoding='utf-8') as f:
            all_lineups = json.load(f)
        
        # Filter for f1.2025 championship
        _lineups_data = [entry for entry in all_lineups if entry.get('Championship') == 'f1.2025']
        
        # Build name index (we'll rely on raw data for number/code/nationality)
        for entry in _lineups_data:
            driver_name = entry.get('Driver', '')
            if driver_name:
                _by_name[normalize_key(driver_name)] = {
                    "Name": driver_name,
                    "Team": entry.get('Team', ''),
                    "SeatType": entry.get('SeatType', 'Primary')
                }
        
        log.info(f"Drivers loaded: {len(_lineups_data)} drivers from 2025 lineup")
    except FileNotFoundError:
        log.error(f"lineups.f1.json not found: {LINEUPS_FILE}")
        _lineups_data = []
    
    # Load drivers.json (full driver details including Nationality)
    try:
        with open(DRIVERS_FILE, 'r', encoding='utf-8') as f:
            drivers_raw = json.load(f)
        
        for driver in drivers_raw:
            name = driver.get('Name', '')
            if name:
                _drivers_full[normalize_key(name)] = driver
        
        log.info(f"Full driver details loaded: {len(_drivers_full)} drivers")
    except FileNotFoundError:
        log.warning(f"drivers.json not found: {DRIVERS_FILE} (Nationality data unavailable)")
        _drivers_full = {}
    
    # Load driver_alias_map.json
    try:
        with open(ALIAS_FILE, 'r', encoding='utf-8') as f:
            raw_aliases = json.load(f)
        
        # Normalize alias keys
        for key, variations in raw_aliases.items():
            normalized_key = normalize_key(key)
            _alias_map[normalized_key] = [normalize_key(v) for v in variations]
        
        log.info(f"Driver aliases loaded: {len(_alias_map)} aliases")
    except FileNotFoundError:
        log.warning(f"driver_alias_map.json not found: {ALIAS_FILE} (optional)")
        _alias_map = {}
    
    _loaded = True


# Load on import
_load_data()


def get_driver_by_number(number: int, year: int = 2025) -> Optional[dict]:
    """Get driver info by race number.
    
    Note: lineups.f1.json doesn't contain numbers. This returns None.
    Use get_driver_by_name() with raw data instead.
    
    Args:
        number: Race number (e.g., 1, 44, 63)
        year: Season year (currently only 2025 supported)
    
    Returns:
        None (lineups.f1.json lacks this data)
    """
    log.warning(f"get_driver_by_number not supported (lineups.f1.json lacks number data)")
    return None


def get_driver_by_code(code: str, year: int = 2025) -> Optional[dict]:
    """Get driver info by 3-letter code.
    
    Note: lineups.f1.json doesn't contain codes. This returns None.
    Use get_driver_by_name() with raw data instead.
    
    Args:
        code: Driver code (e.g., "VER", "HAM", "NOR")
        year: Season year (currently only 2025 supported)
    
    Returns:
        None (lineups.f1.json lacks this data)
    """
    log.warning(f"get_driver_by_code not supported (lineups.f1.json lacks code data)")
    return None


def get_driver_by_name(name: str, year: int = 2025) -> Optional[dict]:
    """Get driver info by name (diacritic-robust).
    
    Note: lineups.f1.json only contains driver names, not full details.
    Returns basic info (Name, Team) if found.
    
    Args:
        name: Driver name (full or last name)
              Examples: "Max Verstappen", "verstappen", "Pérez"
        year: Season year (currently only 2025 supported)
    
    Returns:
        Driver dict with Name/Team or None if not found
    """
    if year != 2025:
        log.warning(f"Only 2025 season supported, got year={year}")
        return None
    
    normalized = normalize_key(name)
    
    # Direct lookup
    driver = _by_name.get(normalized)
    if driver:
        return driver
    
    # Try alias map
    if normalized in _alias_map:
        for variation in _alias_map[normalized]:
            if variation in _by_name:
                return _by_name[variation]
    
    # Partial match (last name)
    for name_key, driver_info in _by_name.items():
        if normalized in name_key or name_key in normalized:
            log.debug(f"Partial match: {name} -> {driver_info['Name']}")
            return driver_info
    
    log.warning(f"Driver not found by name: {name} (normalized: {normalized})")
    return None


def get_driver(raw: object, year: int = 2025) -> Optional[dict]:
    """Universal driver lookup.
    
    Note: Only name lookup works (lineups.f1.json limitation).
    
    Args:
        raw: Can be:
            - str: name
            - dict: with 'name' key
        year: Season year
    
    Returns:
        Driver dict or None
    """
    if isinstance(raw, str):
        return get_driver_by_name(raw, year)
    
    if isinstance(raw, dict):
        name = raw.get('name') or raw.get('Name') or raw.get('fullName')
        if name:
            return get_driver_by_name(name, year)
    
    log.warning(f"Driver lookup failed for: {raw}")
    return None


def list_all_drivers(year: int = 2025) -> list[dict]:
    """Get all drivers for a season.
    
    Args:
        year: Season year (currently only 2025 supported)
    
    Returns:
        List of driver dicts (Name/Team only)
    """
    if year != 2025:
        log.warning(f"Only 2025 season supported, got year={year}")
        return []
    
    return list(_by_name.values())


def get_driver_full_info(name: str) -> Optional[dict]:
    """Get full driver info including Nationality from drivers.json.
    
    Args:
        name: Driver name (full or partial)
    
    Returns:
        Full driver dict with Name, Nationality, RaceNumber, jolpicaId, etc.
        or None if not found
    """
    normalized = normalize_key(name)
    
    # Direct lookup
    driver = _drivers_full.get(normalized)
    if driver:
        return driver
    
    # Partial match
    for name_key, driver_info in _drivers_full.items():
        if normalized in name_key or name_key in normalized:
            return driver_info
    
    return None
