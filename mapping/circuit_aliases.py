"""Circuit name resolution with STRICT matching.

Maps circuit identifiers to (TrackName, TrackUniqueName) with exact matching.
NO fuzzy matching, NO partial matches - hard-fail on mismatch.
"""

import json
from pathlib import Path
from typing import Tuple
from functools import lru_cache

from mapping.normalize import normalize_key
from utils.logging_setup import get_logger

log = get_logger(__name__)

# Load circuits.json once at module level
CIRCUITS_FILE = Path(__file__).parent / "circuits.json"
_circuits_data = None
_circuit_map = {}
_unique_map = {}


def _load_circuits():
    """Load circuits.json and build lookup maps."""
    global _circuits_data, _circuit_map, _unique_map
    
    if _circuits_data is not None:
        return
    
    try:
        with open(CIRCUITS_FILE, 'r', encoding='utf-8') as f:
            _circuits_data = json.load(f)
        
        # Build lookup maps
        for circuit in _circuits_data:
            circuit_name = circuit.get('CircuitName', '')
            unique_name = circuit.get('UniqueName', '')
            jolpica_id = circuit.get('jolpicaCircuitId', '')
            aliases = circuit.get('Aliases', [])
            
            if not circuit_name or not unique_name:
                log.warning(f"Circuit entry missing required fields: {circuit}")
                continue
            
            # CircuitName map (normalized)
            normalized_name = normalize_key(circuit_name)
            if normalized_name:
                _circuit_map[normalized_name] = circuit
            
            # UniqueName map (normalized)
            normalized_unique = normalize_key(unique_name)
            if normalized_unique:
                _unique_map[normalized_unique] = circuit
            
            # Jolpica ID map
            if jolpica_id:
                normalized_id = normalize_key(jolpica_id)
                if normalized_id:
                    _circuit_map[normalized_id] = circuit
            
            # Aliases map (NEW: Support for FastF1 event names like "Spanish Grand Prix")
            for alias in aliases:
                if alias:
                    normalized_alias = normalize_key(alias)
                    if normalized_alias:
                        _circuit_map[normalized_alias] = circuit
        
        log.info(f"Circuits loaded: {len(_circuits_data)} total, {len(_circuit_map)} names, {len(_unique_map)} unique")
        
    except FileNotFoundError:
        log.error(f"circuits.json not found at path: {str(CIRCUITS_FILE)}")
        _circuits_data = []


# Ensure circuits loaded on import
_load_circuits()


def get_circuit(raw: object) -> Tuple[str, str]:
    """Get circuit as (TrackName, TrackUniqueName) with STRICT matching.
    
    **CRITICAL**: This function enforces EXACT matching. No fuzzy logic, no partial
    matches, no guessing. If the circuit is not found in circuits.json, it raises
    ValueError with detailed error message.
    
    Resolution order:
    1. Match by jolpicaCircuitId
    2. Match by CircuitName (normalized)
    3. Match by UniqueName (normalized)
    4. **HARD-FAIL**: Raise ValueError if no match found
    
    Args:
        raw: Can be:
            - dict with 'circuitId', 'CircuitName', 'UniqueName'
            - string (circuit ID or name)
            
    Returns:
        Tuple of (TrackName, TrackUniqueName) from circuits.json
        
    Raises:
        ValueError: If circuit cannot be matched (STRICT requirement)
    """
    if not raw:
        msg = "Empty circuit input - cannot proceed with STRICT matching"
        log.error(f"{msg}: {raw}")
        raise ValueError(msg)
    
    # Dict input
    if isinstance(raw, dict):
        # Try jolpicaCircuitId first
        circuit_id = raw.get('circuitId') or raw.get('jolpicaCircuitId')
        if circuit_id:
            result = _resolve_circuit(circuit_id, raw)
            if result:
                return result
        
        # Try CircuitName
        circuit_name = raw.get('CircuitName') or raw.get('name')
        if circuit_name:
            result = _resolve_circuit(circuit_name, raw)
            if result:
                return result
        
        # Try UniqueName
        unique_name = raw.get('UniqueName')
        if unique_name:
            result = _resolve_circuit(unique_name, raw)
            if result:
                return result
        
        msg = f"Circuit dict has no matching entry in circuits.json"
        log.error(f"{msg}: {str(raw)[:200]}")
        raise ValueError(f"{msg}: {raw}")
    
    # String input
    if isinstance(raw, str):
        result = _resolve_circuit(raw, raw)
        if result:
            return result
        
        msg = f"Circuit string not found in circuits.json (STRICT mode)"
        log.error(f"{msg}: '{raw}' (normalized: {normalize_key(raw)})")
        raise ValueError(f"{msg}: '{raw}'")
    
    msg = f"Unsupported circuit input type: {type(raw).__name__}"
    log.error(msg)
    raise ValueError(msg)


def _resolve_circuit(circuit_str: str, raw_context: object) -> Tuple[str, str] | None:
    """Resolve circuit string to (CircuitName, UniqueName) or None.
    
    Args:
        circuit_str: String to resolve
        raw_context: Original input for error context
        
    Returns:
        Tuple of (CircuitName, UniqueName) or None if not found
    """
    if not circuit_str:
        return None
    
    normalized = normalize_key(circuit_str)
    
    # Try as CircuitName or jolpicaCircuitId
    if normalized in _circuit_map:
        circuit = _circuit_map[normalized]
        return (circuit['CircuitName'], circuit['UniqueName'])
    
    # Try as UniqueName
    if normalized in _unique_map:
        circuit = _unique_map[normalized]
        return (circuit['CircuitName'], circuit['UniqueName'])
    
    return None


def list_available_circuits() -> list[dict]:
    """List all available circuits from circuits.json.
    
    Useful for debugging when STRICT matching fails.
    
    Returns:
        List of circuit dicts with CircuitName, UniqueName, jolpicaCircuitId
    """
    if not _circuits_data:
        return []
    
    return [
        {
            'CircuitName': c.get('CircuitName', ''),
            'UniqueName': c.get('UniqueName', ''),
            'jolpicaCircuitId': c.get('jolpicaCircuitId', '')
        }
        for c in _circuits_data
    ]
