# api/export_service.py
from __future__ import annotations
from pathlib import Path
from typing import Literal, Optional, Dict, Any, cast
import sys
import json
import re
import copy
from utils.logging_setup import get_logger

# Initialize logger
log = get_logger(__name__)

# Robust import (absolute for app runtime, relative for package context)
try:
    from api.providers.router import get_provider  # type: ignore
    from export.rlt_adapter import build_rlt_session  # type: ignore
except Exception:  # pragma: no cover
    from .providers.router import get_provider  # type: ignore
    from export.rlt_adapter import build_rlt_session  # type: ignore

# Session Group Mapping - User selects groups, system exports individual sessions
SESSION_GROUPS = {
    "Practice": ["FP1", "FP2", "FP3"],
    "Qualifying": ["Q"],  # ✅ Fixed: Single "Q" triggers FastF1 split into Q1/Q2/Q3
    "Sprint": ["SQ", "S"],  # Sprint Qualifying + Sprint Race
    "Race": ["R"],
    "All Sessions": ["FP1", "FP2", "FP3", "SQ", "S", "Q", "R"]  # Sprint weekend order: FP1, SQ, S, Q, R
}

def expand_session_group(session_input: str) -> list[str]:
    """
    Expand session group to individual sessions.
    
    Args:
        session_input: Either a group name (Practice, Qualifying, etc.) or individual session code
        
    Returns:
        List of individual session codes to export
    """
    if session_input in SESSION_GROUPS:
        return SESSION_GROUPS[session_input]
    
    # If it's not a group, assume it's an individual session code
    return [session_input]

SessionType = Literal["FP1", "FP2", "FP3", "Q1", "Q2", "Q3", "P", "Q", "SQ", "SS", "S", "R"]

def resource_path(rel: str) -> Path:
    """Pfad-Resolver für PyInstaller (_MEIPASS) und Dev-Run."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return (base / rel).resolve()

# Optional: zentrale Loader für deine JSON-Mappings
def load_json(rel: str):
    with open(resource_path(rel), "r", encoding="utf-8") as f:
        return json.load(f)

def safe_name(s: str) -> str:
    """Convert string to safe filename by removing special characters"""
    s = s.strip()
    # Remove special characters, keep only word chars, spaces, hyphens, dots
    s = re.sub(r"[^\w\s\-.]", "", s)
    # Replace multiple spaces with single underscore
    s = re.sub(r"\s+", "_", s)
    return s

def build_output_name(season: int, round_no: int, session: str, quali_phase: Optional[str], event: Dict[str, Any]) -> str:
    """Build output filename with circuit name instead of round number"""
    # Extract circuit name from event data
    circuit = ""
    if "Circuit" in event:
        circuit = event["Circuit"].get("circuitName", "")
    elif "circuitName" in event:
        circuit = event["circuitName"]  
    elif "raceName" in event:
        circuit = event["raceName"]
    
    if not circuit:
        circuit = f"Round_{round_no}"
        
    circuit = safe_name(circuit)
    
    # Build filename based on session and quali phase / extended codes
    # Qualifying phases
    if session in {"Q1", "Q2", "Q3"}:
        return f"{season}_{circuit}_{session}.json"
    if session == "Q" and quali_phase:
        return f"{season}_{circuit}_Qualifying_{quali_phase}.json"
    if session == "Q":
        return f"{season}_{circuit}_Qualifying.json"
    # Practice sessions
    if session in {"FP1", "FP2", "FP3"}:
        return f"{season}_{circuit}_{session}.json"
    if session == "P":
        return f"{season}_{circuit}_Practice.json"
    # Sprint variants
    if session == "SQ":
        return f"{season}_{circuit}_Sprint_Qualifying.json"
    if session == "SS":
        return f"{season}_{circuit}_Sprint_Shootout.json"
    if session in {"S", "SR"}:
        return f"{season}_{circuit}_Sprint_Race.json"
    # Main race
    if session == "R":
        return f"{season}_{circuit}_Race.json"
    # Fallback
    return f"{season}_{circuit}_{session}.json"

def unique_path(directory: Path, filename: str) -> Path:
    """Generate unique path to avoid filename collisions"""
    path = directory / filename
    if not path.exists():
        return path
        
    # Add counter suffix
    stem = path.stem
    suffix = path.suffix
    counter = 2
    
    while True:
        candidate = directory / f"{stem}_{counter:02d}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

def _infer_session_type(session: str) -> str:
    """Infer session_type for RLT from session code"""
    if session in {"Q", "Q1", "Q2", "Q3"}:
        return "Qualification"
    elif session in {"P", "FP1", "FP2", "FP3"}:
        return "Practice"
    elif session in {"R"}:
        return "Race"
    elif session in {"SQ", "SS", "S", "SR"}:
        return "Sprint"
    return "Race"  # Default

def session_allowed_by_schedule(season: int, round_no: int, session: str) -> bool:
    """Check if session is allowed based on race schedule (for Sprint validation)"""
    if session != "SQ":
        return True  # Non-sprint sessions are always allowed
        
    try:
        provider = get_provider(year=season)
        schedule_data = provider.schedule(season)
        event = next((x for x in schedule_data if int(x.get("round", 0)) == round_no), None)
        return bool(event and event.get("hasSprint", False))
    except Exception:
        # In case of error, don't block the export
        return True

def _find_event(season: int, round_no: int) -> Dict[str, Any]:
    """Find event info for round"""
    try:
        provider = get_provider(year=season)
        schedule_data = provider.schedule(season)
        return next((x for x in schedule_data if int(x.get("round", 0)) == round_no), {})
    except Exception:
        return {}

# Haupt-API mit Dual-Source Aggregation
def run_export(season: int, round_no: int, session: SessionType, out_dir: Path, verbose: bool=False) -> Optional[Path]:
    """
    Modernized export with Dual-Source Aggregation (Jolpica + FastF1).
    Uses circuit names in filenames and robust provider fallback.
    
    Special handling for Qualifying:
    - If session='Q', exports 3 separate files: Q1.json, Q2.json, Q3.json
    - Each file contains only drivers who participated in that session
    - QualType is set to Q1/Q2/Q3 respectively
    
    Args:
        season: Year (e.g., 2024)
        round_no: Round number (1-24)
        session: Session code ("R", "Q", "Q1", "Q2", "Q3", "FP1", etc.)
        out_dir: Output directory for JSON files
        verbose: Print progress messages
    
    Returns:
        Path to exported JSON file (or last file if multiple), or None if failed
    """
    
    # 🔧 QUALIFYING SPECIAL HANDLING: FastF1 can split Q into Q1/Q2/Q3, Jolpica cannot
    if session == 'Q':
        provider = get_provider(year=season)
        provider_name = getattr(provider, 'name', 'unknown')
        
        # FastF1: Split into 3 separate files with Q1/Q2/Q3 times
        if provider_name == 'fastf1':
            log.info(f"Qualifying with FastF1: will split into Q1, Q2, Q3")
            # Set flag to handle after data fetch
            qual_split_mode = True
        else:
            # Jolpica: Single file with final results
            log.info(f"Qualifying with Jolpica: single results file (no Q1/Q2/Q3 split)")
            qual_split_mode = False
    else:
        qual_split_mode = False
    
    # Normal single-session export continues below...
    out_dir.mkdir(parents=True, exist_ok=True)

    # Session validation: accept extended codes and groups expanded by GUI
    valid_sessions = {"FP1", "FP2", "FP3", "Q1", "Q2", "Q3", "P", "Q", "SQ", "SS", "S", "R"}
    if session not in valid_sessions:
        raise ValueError(f"Invalid session type: {session}. Must be one of {valid_sessions}")

    # Get event info for filename
    event = _find_event(season, round_no)

    # Sprint validation with event info
    if session == "SQ":
        has_sprint = event.get("hasSprint", False) or "sprint" in str(event.get("EventFormat", "")).lower()
        if not has_sprint:
            log.warning(f"Sprint not scheduled but attempting export: season={season}, round={round_no}")
            if verbose:
                print("⚠️ Sprint not scheduled for this round, but attempting export anyway...")

    # Get data via Provider (handles normalization per provider)
    log.debug(f"Building payload: season={season}, round={round_no}, session={session}")
    provider = get_provider(year=season)
    payload = provider.fetch_session_raw(season, round_no, session)
    
    if not payload or not payload.get("Drivers"):
        log.warning(f"No data available from any source: season={season}, round={round_no}, session={session}")
        if verbose:
            print(f"ℹ️ No data available from any source for {season} R{round_no} {session}")
        return None
        
    # Log source info
    source = payload.get("source", payload.get("provider", "unknown"))
    driver_count = len(payload.get("Drivers") or [])
    log.info(f"Data retrieved: season={season}, round={round_no}, session={session}, source={source}, driver_count={driver_count}")
    if verbose:
        print(f"✓ Data from {source}: {driver_count} drivers")

    # 🔥 CRITICAL: Enrich payload with metadata for RLT adapter
    # The adapter needs: circuit, session_type, race_type, qual_type, date
    # Priority: circuitFullName > Circuit.circuitName > circuitName > raceName (fallback)
    circuit_name = (
        event.get("circuitFullName") or 
        event.get("Circuit", {}).get("circuitName") or 
        event.get("circuitName") or 
        event.get("raceName", "Unknown")
    )
    
    # 🔧 Clean FastF1 format: "Sakhir (Bahrain)" → "Sakhir"
    # This ensures compatibility with circuits.json aliases
    import re
    circuit_name = re.sub(r'\s*\(.*?\)\s*$', '', circuit_name).strip()
    
    payload.setdefault("circuit", circuit_name)
    payload.setdefault("Circuit", event.get("Circuit", {}))
    payload.setdefault("session_type", _infer_session_type(session))
    payload.setdefault("race_type", "Regular")  # Could enhance with Sprint detection
    payload.setdefault("qual_type", session if session in {"Q1", "Q2", "Q3"} else None)
    payload.setdefault("date", event.get("date"))
    payload.setdefault("season", season)
    payload.setdefault("round", round_no)

    # � QUALIFYING SPLIT: Create 3 separate files for FastF1 Q sessions
    if qual_split_mode and session == 'Q':
        if verbose:
            print(f"📋 Splitting qualifying into Q1, Q2, Q3...")
        
        results = []
        for q_session in ['Q1', 'Q2', 'Q3']:
            try:
                # Create payload for this Q session - DEEP COPY to preserve driver data
                q_payload = copy.deepcopy(payload)  # 🔥 CRITICAL: Must be deep copy!
                q_payload['qual_type'] = q_session
                q_payload['session_type'] = 'Qualification'
                q_payload['_current_q_session'] = q_session  # Marker for rlt_adapter
                
                # Transform and export
                rlt_payload = build_rlt_session(q_payload)
                filename = build_output_name(season, round_no, q_session, None, event)
                output_path = out_dir / filename
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(rlt_payload, f, indent=2, ensure_ascii=False)
                
                size = output_path.stat().st_size
                log.info(f"Export successful: season={season}, round={round_no}, session={q_session}, output={output_path}, size_bytes={size}")
                results.append(output_path)
                
                if verbose:
                    print(f"  ✓ {q_session}: {output_path.name}")
                    
            except Exception as e:
                log.exception(f"Failed to export {q_session}: {e}")
                if verbose:
                    print(f"  ⚠️ {q_session} failed: {e}")
        
        if results:
            if verbose:
                print(f"✅ Exported {len(results)} qualifying sessions")
            return results[-1]
        else:
            if verbose:
                print(f"❌ No qualifying sessions exported")
            return None

    # �🔥 CRITICAL FIX: Transform to RLT Admin-Spec format BEFORE writing
    try:
        log.debug(f"Transforming to RLT format: season={season}, round={round_no}, session={session}")
        rlt_payload = build_rlt_session(payload)
        if verbose:
            print(f"✓ Transformed to RLT Admin-Spec format")
    except Exception as e:
        log.exception(f"RLT transformation failed: season={season}, round={round_no}, session={session}")
        if verbose:
            print(f"❌ RLT transformation failed: {e}")
        raise e

    # 🔧 QUALIFYING SPLIT: If session='Q', create 3 separate files (Q1, Q2, Q3)
    if session == 'Q':
        if verbose:
            print(f"📋 Splitting Qualifying into Q1, Q2, Q3...")
        
        results = []
        for q_phase in ['Q1', 'Q2', 'Q3']:
            # Filter drivers: only those with a time in this phase
            filtered_drivers = []
            for driver in rlt_payload.get('Drivers', []):
                q_time = driver.get(q_phase)
                if q_time and q_time != "0:00.000":
                    # Create copy and set TimeInt to this phase's time
                    driver_copy = driver.copy()
                    # Parse Q-time to milliseconds
                    from export.rlt_adapter import _to_milliseconds
                    q_time_ms = _to_milliseconds(q_time)
                    driver_copy['TimeInt'] = q_time_ms
                    driver_copy['FastestLapTimeInt'] = q_time_ms
                    filtered_drivers.append(driver_copy)
            
            if not filtered_drivers:
                log.warning(f"No drivers with {q_phase} times")
                if verbose:
                    print(f"  ⚠️ {q_phase}: No drivers")
                continue
            
            # Create payload for this phase
            q_payload = rlt_payload.copy()
            q_payload['Drivers'] = filtered_drivers
            q_payload['QualType'] = q_phase
            
            # Generate filename
            filename = build_output_name(season, round_no, q_phase, None, event)
            output_path = unique_path(out_dir, filename)
            
            # Write JSON
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(q_payload, f, indent=2, ensure_ascii=False)
                
                results.append(output_path)
                log.info(f"Exported {q_phase}: {output_path}, {len(filtered_drivers)} drivers")
                if verbose:
                    print(f"  ✓ {q_phase}: {output_path.name} ({len(filtered_drivers)} drivers)")
            except Exception as e:
                log.error(f"Failed to write {q_phase}: {e}")
                if verbose:
                    print(f"  ❌ {q_phase} failed: {e}")
        
        if results:
            if verbose:
                print(f"✅ Exported {len(results)} qualifying phases")
            return results[-1]  # Return last file
        else:
            if verbose:
                print(f"❌ No qualifying data")
            return None
    
    # Normal single-session export: Generate filename with circuit name
    filename = build_output_name(season, round_no, session, None, event)
        
    # Generate unique path to avoid collisions
    output_path = unique_path(out_dir, filename)
    
    # Write JSON (NOW RLT-compliant!)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rlt_payload, f, indent=2, ensure_ascii=False)
        
        log.info(f"Export successful: season={season}, round={round_no}, session={session}, output={str(output_path)}, size_bytes={output_path.stat().st_size}")
        if verbose:
            print(f"✅ Exported {session}: {output_path}")
            
        return output_path
        
    except Exception as e:
        log.exception(f"Export failed: season={season}, round={round_no}, session={session}, output={str(output_path)}")
        if verbose:
            print(f"❌ Export failed: {e}")
        raise e
