# api/providers/fastf1_provider.py  
"""FastF1 provider for F1 data with caching and robust session loading"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from pathlib import Path
import os
from .base import SessionType

def _cache_dir() -> Path:
    """Get FastF1 cache directory"""
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    cache_dir = base / "LooneyF1Tool" / "fastf1_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def _ff1_candidates(session: SessionType) -> List[str]:
    """Get list of possible FastF1 session codes to try"""
    if session == "Q":  
        return ["Q"]
    if session == "R":  
        return ["R"] 
    if session == "P":  
        return ["FP1"]  # Could expand to ["FP1","FP2","FP3"]
    if session == "SQ": 
        return ["SQ", "SS", "S"]  # Try different sprint naming conventions
    return [session]

def schedule(season: int) -> List[Dict[str, Any]]:
    """Get race schedule from FastF1"""
    try:
        import fastf1
        
        # Enable caching
        fastf1.Cache.enable_cache(str(_cache_dir()))
        
        # Get event schedule
        df = fastf1.get_event_schedule(season)
        
        rows: List[Dict[str, Any]] = []
        for _, event in df.iterrows():
            round_no = int(event.get("RoundNumber", 0))
            if round_no <= 0:
                continue
                
            event_format = str(event.get("EventFormat", "") or "")
            has_sprint = "sprint" in event_format.lower()
            
            rows.append({
                "round": round_no,
                "date": str(event.get("EventDate", "")),
                "raceName": event.get("EventName", ""),
                "Circuit": {
                    "circuitName": f"{event.get('Location', '')} ({event.get('Country', '')})"
                },
                "EventFormat": event_format,
                "hasSprint": has_sprint
            })
            
        # Sort by round number
        rows.sort(key=lambda r: r["round"])
        return rows
        
    except Exception:
        return []

def export_payload(season: int, round_no: int, session: SessionType) -> Optional[Dict[str, Any]]:
    """Get export payload from FastF1 with robust session loading"""
    try:
        import fastf1
        
        # Enable caching
        fastf1.Cache.enable_cache(str(_cache_dir()))
        
        # Get event info for circuit metadata
        try:
            event = fastf1.get_event(season, round_no)
            event_name = event.EventName  # "Spanish Grand Prix", "Monaco Grand Prix", etc.
            location = event.Location
            country = event.Country
        except Exception:
            event_name = ""
            location = ""
            country = ""
        
        # Try multiple session codes robustly
        last_error = None
        ff1_session = None
        
        for code in _ff1_candidates(session):
            try:
                ff1_session = fastf1.get_session(season, round_no, code)
                ff1_session.load(laps=False, telemetry=False, weather=False, messages=False)
                
                # Check if results are available
                if getattr(ff1_session, "results", None) is not None and not ff1_session.results.empty:
                    # Success! Process this session
                    break
            except Exception as e:
                last_error = e
                continue
        else:
            # All codes failed
            return None
            
        results_df = ff1_session.results
        
        # Check session type for conditional fields
        is_qualification = session in ["Q", "SQ"]
        
        # Convert to drivers list
        drivers = []
        for _, row in results_df.iterrows():
            driver_data = {
                "DriverNumber": str(row.get("DriverNumber", "")),
                "Abbreviation": row.get("Abbreviation", ""),
                "Driver": {
                    "givenName": row.get("FirstName", ""),
                    "familyName": row.get("LastName", "")
                },
                "Team": {  # Normalize to Jolpica format with nested Team object
                    "Name": row.get("TeamName", "")
                },
                "TeamName": row.get("TeamName", ""),  # Keep flat field for compatibility
                "GridPosition": int(row.get("GridPosition", 0)) if "GridPosition" in results_df.columns and not row.isna()["GridPosition"] else None,
                "Position": int(row.get("Position", 0)) if "Position" in results_df.columns and not row.isna()["Position"] else 0,
                "Status": str(row.get("Status", "")),
                "FastestLapTime": str(row.get("FastestLapTime", "")) if "FastestLapTime" in results_df.columns else "",
                # RLT Admin-Spec required fields with defaults
                "SeatType": "Primary",  # Must be string enum: "Primary"|"Reserve"|"NoSeat"
                "LapsCount": 0,    # Would need lap-by-lap data
                "PitsCount": 0,    # Would need pit stop data
            }
            
            # Add Q1/Q2/Q3 ONLY for Qualification sessions (Admin-Spec requirement)
            if is_qualification:
                # Clean NaT values (pandas timestamp artifacts)
                q1_val = str(row.get("Q1", "")) if "Q1" in results_df.columns else ""
                q2_val = str(row.get("Q2", "")) if "Q2" in results_df.columns else ""
                q3_val = str(row.get("Q3", "")) if "Q3" in results_df.columns else ""
                driver_data["Q1"] = "" if q1_val == "NaT" else q1_val
                driver_data["Q2"] = "" if q2_val == "NaT" else q2_val
                driver_data["Q3"] = "" if q3_val == "NaT" else q3_val
            
            # Add time information if available (clean NaT)
            if "Time" in results_df.columns:
                time_val = str(row.get("Time", ""))
                driver_data["Time"] = "" if time_val == "NaT" else time_val
                
            drivers.append(driver_data)
        
        # Return payload in expected format
        return {
            "season": season,
            "round": round_no,
            "session": session,
            "circuit": event_name,  # "Spanish Grand Prix", "Monaco Grand Prix", etc.
            "Circuit": {
                "circuitName": event_name,
                "Location": location,
                "Country": country
            },
            "Drivers": drivers,  # Use capital D to match Jolpica format
            "source": "fastf1"
        }
        
    except Exception:
        return None