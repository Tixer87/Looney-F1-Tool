"""Nationality resolution with unified alias authority.

Maps nationality strings to canonical names and codes using:
1. nations.json (source of truth)
2. nations_alias_map.json (common aliases like "British" → "United Kingdom")

API:
    get_driver_nation(raw) -> dict with {"Name", "Code"}
"""

import json
from pathlib import Path
from mapping.normalize import normalize_key
from utils.logging_setup import get_logger

log = get_logger(__name__)

# Load data once at module level
NATIONS_FILE = Path(__file__).parent / "nations.json"
ALIAS_FILE = Path(__file__).parent / "nations_alias_map.json"

_nations_data = []
_alias_map = {}
_loaded = False

# Indexes for fast lookup
_by_name = {}
_by_code = {}


def _load_data():
    """Load nations.json and nations_alias_map.json."""
    global _nations_data, _alias_map, _loaded
    global _by_name, _by_code
    
    if _loaded:
        return
    
    # Load nations.json
    try:
        with open(NATIONS_FILE, 'r', encoding='utf-8') as f:
            _nations_data = json.load(f)
        
        # Build indexes
        for nation in _nations_data:
            name = nation.get('Name', '')
            code = nation.get('Code', '') or nation.get('ThreeLetterCode', '')
            
            if name:
                _by_name[normalize_key(name)] = nation
            
            if code:
                _by_code[normalize_key(code)] = nation
        
        log.info(f"Nations loaded: {len(_nations_data)} nations")
    except FileNotFoundError:
        log.error(f"nations.json not found: {NATIONS_FILE}")
        _nations_data = []
    
    # Load nations_alias_map.json
    try:
        with open(ALIAS_FILE, 'r', encoding='utf-8') as f:
            raw_aliases = json.load(f)
        
        # Normalize alias keys → canonical name
        for key, canonical_name in raw_aliases.items():
            normalized_key = normalize_key(key)
            _alias_map[normalized_key] = canonical_name
        
        log.info(f"Nation aliases loaded: {len(_alias_map)} mappings")
    except FileNotFoundError:
        log.warning(f"nations_alias_map.json not found: {ALIAS_FILE} (optional)")
        _alias_map = {}
    
    _loaded = True


# Load on import
_load_data()


def get_driver_nation(raw: str) -> dict:
    """Get canonical nationality info.
    
    Resolution order:
    1. Alias map (e.g., "British" → "United Kingdom")
    2. Direct match in nations.json by Name
    3. Direct match in nations.json by Code
    4. Fallback: {"Name": "Unknown", "Code": "UNK"}
    
    Args:
        raw: Nationality string (e.g., "British", "GBR", "United Kingdom")
    
    Returns:
        dict with:
            - Name: Canonical nationality name
            - Code: 3-letter code (or provider code if available)
    
    Examples:
        >>> get_driver_nation("British")
        {"Name": "United Kingdom", "Code": "GBR"}
        
        >>> get_driver_nation("Dutch")
        {"Name": "Netherlands", "Code": "NLD"}
        
        >>> get_driver_nation("United Kingdom")
        {"Name": "United Kingdom", "Code": "GBR"}
    """
    if not raw or not isinstance(raw, str):
        log.warning(f"Invalid nationality input: {raw}")
        return {"Name": "Unknown", "Code": "UNK"}
    
    normalized = normalize_key(raw)
    
    # 1. Try alias map first
    if normalized in _alias_map:
        canonical_name = _alias_map[normalized]
        canonical_normalized = normalize_key(canonical_name)
        
        # Lookup canonical name in nations.json
        if canonical_normalized in _by_name:
            nation = _by_name[canonical_normalized]
            return {
                "Name": nation.get('Name', canonical_name),
                "Code": nation.get('Code') or nation.get('ThreeLetterCode', 'UNK')
            }
        
        # Alias resolved but not in nations.json (use alias target directly)
        log.debug(f"Alias resolved but not in nations.json: {raw} → {canonical_name}")
        return {"Name": canonical_name, "Code": "UNK"}
    
    # 2. Try direct name match
    if normalized in _by_name:
        nation = _by_name[normalized]
        return {
            "Name": nation.get('Name', raw),
            "Code": nation.get('Code') or nation.get('ThreeLetterCode', 'UNK')
        }
    
    # 3. Try direct code match
    if normalized in _by_code:
        nation = _by_code[normalized]
        return {
            "Name": nation.get('Name', raw),
            "Code": nation.get('Code') or nation.get('ThreeLetterCode', 'UNK')
        }
    
    # Fallback
    log.warning(f"Nationality not found: {raw} (normalized: {normalized})")
    return {"Name": raw.strip() if len(raw.strip()) > 2 else "Unknown", "Code": "UNK"}


def list_all_nations() -> list[dict]:
    """Get all nations from nations.json.
    
    Returns:
        List of nation dicts
    """
    return _nations_data.copy()
