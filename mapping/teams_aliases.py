"""Team name resolution with unified alias authority.

Maps constructorId/team names to canonical RLT team info using:
1. teams.f1.json (source of truth for prefixes/abbr)
2. team_alias_map.json (all known aliases including constructor: keys)

API:
    get_team_name(raw, year) -> dict with Name/UniqueName/Abbr
"""

import json
from pathlib import Path
from typing import Optional
from mapping.normalize import normalize_key
from utils.logging_setup import get_logger

log = get_logger(__name__)

# Load data once at module level
TEAMS_FILE = Path(__file__).parent / "teams.f1.json"
ALIAS_FILE = Path(__file__).parent / "team_alias_map.json"

_teams_data = []
_alias_map = {}
_loaded = False


def _load_data():
    """Load teams.f1.json and team_alias_map.json."""
    global _teams_data, _alias_map, _loaded
    
    if _loaded:
        return
    
    # Load teams.f1.json
    try:
        with open(TEAMS_FILE, 'r', encoding='utf-8') as f:
            _teams_data = json.load(f)
        log.info(f"Teams data loaded: {len(_teams_data)} teams")
    except FileNotFoundError:
        log.error(f"teams.f1.json not found: {TEAMS_FILE}")
        _teams_data = []
    
    # Load team_alias_map.json
    try:
        with open(ALIAS_FILE, 'r', encoding='utf-8') as f:
            raw_aliases = json.load(f)
        
        # Normalize all keys
        for key, value in raw_aliases.items():
            normalized = normalize_key(key)
            _alias_map[normalized] = value
        
        log.info(f"Team aliases loaded: {len(_alias_map)} mappings")
    except FileNotFoundError:
        log.error(f"team_alias_map.json not found: {ALIAS_FILE}")
        _alias_map = {}
    
    _loaded = True


# Load on import
_load_data()


def get_team_name(raw: object, year: Optional[int] = None) -> dict:
    """Get canonical team info from various inputs.
    
    Resolution order:
    1. If dict with 'constructorId': lookup "constructor:<id>" in alias map
    2. If string or dict['Name']: normalize and lookup in alias map
    3. Fallback: "Unknown Team"
    
    Args:
        raw: Can be:
            - dict with 'constructorId' and/or 'Name'
            - string (constructor ID or team name)
        year: Season year for UniqueName suffix (e.g., 2025)
    
    Returns:
        dict with:
            - Name: Canonical RLT team name
            - UniqueName: UniquePrefix + year (or prefix without year if year=None)
            - Abbr: Team abbreviation
    
    Examples:
        >>> get_team_name("red_bull", 2025)
        {"Name": "Red Bull", "UniqueName": "red.bull.2025", "Abbr": "RB"}
        
        >>> get_team_name({"constructorId": "rb"}, 2025)
        {"Name": "Racing Bulls", "UniqueName": "racing.bulls.2025", "Abbr": "VRB"}
    """
    if not raw:
        log.warning("Empty team input")
        return {"Name": "Unknown Team", "UniqueName": "Unknown", "Abbr": "UNK"}
    
    # Extract constructor ID and name
    constructor_id = None
    name = None
    
    if isinstance(raw, dict):
        constructor_id = raw.get('constructorId')
        name = raw.get('Name') or raw.get('name')
    elif isinstance(raw, str):
        # Could be constructor ID or name
        name = raw
    else:
        log.warning(f"Unsupported team input type: {type(raw).__name__}")
        return {"Name": "Unknown Team", "UniqueName": "Unknown", "Abbr": "UNK"}
    
    # Try constructor ID first (highest priority)
    if constructor_id:
        key = f"constructor:{constructor_id}".lower()
        normalized = normalize_key(key)
        
        if normalized in _alias_map:
            team_info = _alias_map[normalized]
            unique_name = _build_unique_name(team_info['UniquePrefix'], year)
            return {
                "Name": team_info['Name'],
                "UniqueName": unique_name,
                "Abbr": team_info['Abbr']
            }
    
    # Try name lookup
    if name:
        normalized = normalize_key(name)
        
        if normalized in _alias_map:
            team_info = _alias_map[normalized]
            unique_name = _build_unique_name(team_info['UniquePrefix'], year)
            return {
                "Name": team_info['Name'],
                "UniqueName": unique_name,
                "Abbr": team_info['Abbr']
            }
        
        # Fallback: use raw name if it looks reasonable
        if len(name.strip()) > 2:
            log.warning(f"Team not in alias map: {name} (normalized: {normalized})")
            return {
                "Name": name.strip(),
                "UniqueName": normalize_key(name),
                "Abbr": "UNK"
            }
    
    # Complete fallback
    log.warning(f"Team lookup failed for: {raw}")
    return {"Name": "Unknown Team", "UniqueName": "Unknown", "Abbr": "UNK"}


def _build_unique_name(prefix: str, year: Optional[int]) -> str:
    """Build UniqueName from prefix and year.
    
    Args:
        prefix: Team prefix (e.g., "red.bull.")
        year: Season year or None
    
    Returns:
        UniqueName string (e.g., "red.bull.2025" or "red.bull" if year=None)
    """
    if year is None:
        # Remove trailing dot if present
        return prefix.rstrip('.')
    
    return f"{prefix}{year}"


def list_all_teams() -> list[dict]:
    """Get all teams from teams.f1.json.
    
    Returns:
        List of team dicts from teams.f1.json
    """
    return _teams_data.copy()
