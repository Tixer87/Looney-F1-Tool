"""RLT Session Result adapter with strict schema compliance.

Converts internal session data to RLT JSON format with:
- Robust mapping via getter functions
- Gap calculation (Race vs Quali/Practice logic)
- StintsRaw encoding with numeric tyre types
- Integer millisecond times
- Schema validation
"""

from typing import Any
from datetime import datetime

from export.rlt_enums import (
    SessionType, RaceType, QualType, SessionStatus, SeatType, Status,
    WeatherType, TyreType, TYRE_TYPE_TO_NUM, 
    TOP_LEVEL_REQUIRED, DRIVER_REQUIRED, DRIVER_REQUIRED_QUALI
)
from mapping.drivers_aliases import get_driver_by_number, get_driver_by_code, get_driver_by_name, get_driver_full_info
from mapping.teams_aliases import get_team_name
from mapping.drivers_nations import get_driver_nation
from mapping.circuit_aliases import get_circuit
from utils.logging_setup import get_logger

log = get_logger(__name__)


def format_ms_short(ms: int) -> str:
    """Format milliseconds to RLT short time format: m:ss.mmm
    
    Examples:
        76899 → "1:16.899"
        125450 → "2:05.450"
        59123 → "0:59.123"
    
    Args:
        ms: Time in milliseconds
        
    Returns:
        Formatted time string "m:ss.mmm"
    """
    if not ms or ms < 0:
        return "0:00.000"
    
    s, ms_remainder = divmod(ms, 1000)
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}.{ms_remainder:03d}"


def build_rlt_session(payload: dict) -> dict:
    """Build RLT session result from internal payload.
    
    CRITICAL: Follows Admin-Spec (rlt_import_session_results_json_format.txt) strictly!
    All required fields must be present, even if 0 or default values.
    
    Args:
        payload: Internal session data (e.g., from Jolpica API or CSV import)
        
    Returns:
        RLT-compliant session result dict with ALL required fields from Admin-Spec
        
    Raises:
        ValueError: If required fields missing or circuit not found (STRICT)
    """
    log.info(f"Building RLT session: session_type={payload.get('session_type')}")
    
    # Extract session metadata
    session_type = _map_session_type(payload.get('session_type'))
    race_type = _map_race_type(payload.get('race_type'))
    qual_type = _map_qual_type(payload.get('qual_type')) if session_type == "Qualification" else None
    current_q_session = payload.get('_current_q_session')  # Q1, Q2, or Q3 (for FastF1 split mode)
    
    # 🔥 CRITICAL: RLT uses "Regular" for RaceType, not "Main"
    if race_type == "Main":
        race_type = "Regular"
    
    # 🔥 CRITICAL: SessionPosition must be 0, 1, 2 for Q1, Q2, Q3
    session_position = payload.get('session_position') or payload.get('SessionPosition') or 1
    if current_q_session == 'Q1':
        session_position = 0
    elif current_q_session == 'Q2':
        session_position = 1
    elif current_q_session == 'Q3':
        session_position = 2
    
    # Circuit (STRICT - will raise ValueError if not found)
    circuit_raw = payload.get('circuit') or payload.get('Circuit')
    track_name, track_unique = get_circuit(circuit_raw)
    
    # Date/Time (ISO 8601 format required)
    date_str = payload.get('date') or payload.get('Date')
    if not date_str:
        log.warning("No date provided, using current datetime")
        date_str = datetime.utcnow().isoformat() + 'Z'
    else:
        # Ensure ISO format with 'T' separator and 'Z' timezone
        if 'T' not in date_str:
            # Convert "2025-03-16 00:00:00" to "2025-03-16T00:00:00Z"
            date_str = date_str.replace(' ', 'T')
        if not date_str.endswith('Z'):
            date_str = date_str.rstrip('Z') + 'Z'
    
    # Drivers
    drivers_raw = payload.get('drivers') or payload.get('Drivers') or []
    
    # 🔥 CRITICAL: Filter RAW drivers BEFORE _build_driver (which removes Q fields)
    # Q1: All drivers with Q1 time, Q2: All with Q2 time, Q3: All with Q3 time
    # FastF1 provides Q1/Q2/Q3 as string fields (e.g., "0 days 00:01:16.899000000")
    if current_q_session:
        original_count = len(drivers_raw)
        if current_q_session == 'Q1':
            # Q1: Only drivers who have a Q1 time (participated in Q1)
            drivers_raw = [d for d in drivers_raw if d.get('Q1') and str(d.get('Q1')).strip() not in ['', 'NaT', 'None', '0']]
        elif current_q_session == 'Q2':
            # Q2: Only drivers who have a Q2 time (advanced from Q1)
            drivers_raw = [d for d in drivers_raw if d.get('Q2') and str(d.get('Q2')).strip() not in ['', 'NaT', 'None', '0']]
        elif current_q_session == 'Q3':
            # Q3: Only drivers who have a Q3 time (advanced from Q2)
            drivers_raw = [d for d in drivers_raw if d.get('Q3') and str(d.get('Q3')).strip() not in ['', 'NaT', 'None', '0']]
        
        if len(drivers_raw) < original_count:
            log.info(f"Filtered {current_q_session}: {original_count} → {len(drivers_raw)} drivers (time-based knockout)")
    
    drivers = []
    
    for driver_raw in drivers_raw:
        # Pass current_q_session to filter drivers by participation
        driver = _build_driver(driver_raw, session_type, current_q_session)
        if driver:
            drivers.append(driver)
    
    if not drivers:
        log.warning("No drivers in session")
    
    # 🔥 CRITICAL: Sort by TimeInt and reassign positions for qualifying split mode
    if current_q_session and drivers:
        # Sort by TimeInt (fastest first, 0 values go to end)
        drivers.sort(key=lambda d: d.get('TimeInt', 999999999) if d.get('TimeInt', 0) > 0 else 999999999)
        # Reassign positions based on sorted order
        for idx, driver in enumerate(drivers, start=1):
            driver['Position'] = idx
    
    # Calculate gaps
    if session_type == "Race":
        drivers = _calculate_gaps_race(drivers)
    elif session_type in ["Qualification", "Practice"]:
        drivers = _calculate_gaps_quali(drivers)
    
    # Build top-level result IN EXACT ORDER matching working RLT files
    # CRITICAL: RLT parser expects fields in this exact order!
    result = {
        "SessionType": session_type,
        "RaceType": race_type,
        "QualType": qual_type or "Regular",  # Always include, even for Race
        "SessionStatus": payload.get('session_status') or payload.get('SessionStatus') or "FullPoints",
        "SessionPosition": session_position,
        "FastestLapTimeInt": 0,  # Will be calculated from drivers
        "FastestLapNumLap": 0,
        "TrackName": track_name,
        "TrackUniqueName": track_unique,
        "IsLiveData": payload.get('is_live') or payload.get('IsLiveData') or False,
        "LiveRecordPercent": payload.get('live_record_percent') or payload.get('LiveRecordPercent') or 0,
        "IsLiveFullRecord": payload.get('is_live_full_record') or payload.get('IsLiveFullRecord') or False,
        "IsSingleplayerMode": payload.get('is_singleplayer') or payload.get('IsSingleplayerMode') or False,
        "WeatherType": "Clear",  # Will be overridden below if present in payload
        "AirTemperature": 0,
        "TrackTemperature": 0,
        "TotalLaps": payload.get('total_laps') or payload.get('TotalLaps') or max((d.get('laps', 0) for d in drivers_raw), default=0),
        "SessionDuration": "00:00:00",
        "Drivers": drivers
    }
    
    # Calculate session-level fastest lap from drivers
    if drivers:
        fastest_times = [d.get('FastestLapTimeInt', 0) for d in drivers if d.get('FastestLapTimeInt', 0) > 0]
        if fastest_times:
            result["FastestLapTimeInt"] = min(fastest_times)
            # Find driver with fastest lap
            for d in drivers:
                if d.get('FastestLapTimeInt') == result["FastestLapTimeInt"]:
                    result["FastestLapNumLap"] = d.get('FastestLapNumLap', 0)
                    break
    
    # Optional fields from payload (override defaults if present)
    if 'weather' in payload or 'WeatherType' in payload:
        weather = _map_weather(payload.get('weather') or payload.get('WeatherType'))
        if weather:
            result["WeatherType"] = weather
    
    if 'air_temp' in payload or 'AirTemperature' in payload:
        result["AirTemperature"] = int(payload.get('air_temp') or payload.get('AirTemperature') or 0)
    
    if 'track_temp' in payload or 'TrackTemperature' in payload:
        result["TrackTemperature"] = int(payload.get('track_temp') or payload.get('TrackTemperature') or 0)
    
    if 'session_duration' in payload or 'SessionDuration' in payload:
        result["SessionDuration"] = payload.get('session_duration') or payload.get('SessionDuration') or "00:00:00"
    
    _validate_required_fields(result)
    
    log.info(f"RLT session built: {len(drivers)} drivers, track={track_name}")
    
    #  CRITICAL: RLT expects top-level session fields, NO "Session" wrapper!
    # Admin-Spec shows: {"SessionType": "Race", ...} NOT {"Session": {"SessionType": "Race", ...}}
    return result


def _build_driver(driver_raw: dict, session_type: str = "Race", current_q_session: str | None = None) -> dict | None:
    """Build driver block from raw driver data.
    
    CRITICAL: driver_block.py already builds RLT-like structures!
    This function now ENRICHES them with:
    - Canonical driver names via get_driver_by_name()
    - Nationality via get_driver_nation() (from _nationality_raw passed by driver_block)
    - Team validation via get_team_name() (from _constructorId passed by driver_block)
    - Q1/Q2/Q3 fields for Qualification sessions (MANDATORY Q1)
    - Status="Ok" for Qualification (Admin-Spec requirement)
    
    Args:
        driver_raw: Driver dict from build_driver_blocks() (already RLT-like with _raw fields)
        session_type: "Race" | "Qualification" | "Practice" (for quali-specific fields)
        
    Returns:
        RLT driver dict or None if critical data missing
    """
    # Check if this is already an RLT-like structure from driver_block.py
    if 'Driver' in driver_raw and isinstance(driver_raw['Driver'], dict):
        # Already preprocessed by driver_block.py
        year = 2025
        
        # Extract current values - handle both formats (driver_block.py and FastF1 provider)
        if 'Name' in driver_raw['Driver']:
            # driver_block.py format: Driver.Name
            current_name = driver_raw['Driver']['Name']
        elif 'givenName' in driver_raw['Driver'] and 'familyName' in driver_raw['Driver']:
            # FastF1 provider format: Driver.givenName + Driver.familyName
            current_name = f"{driver_raw['Driver']['givenName']} {driver_raw['Driver']['familyName']}".strip()
        else:
            current_name = 'Unknown Driver'
        
        driver_number = driver_raw.get('RaceNumber') or driver_raw.get('DriverNumber')
        
        # Extract raw Jolpica data (passed via _nationality_raw and _constructorId)
        nationality_raw = driver_raw['Driver'].get('_nationality_raw', '')
        constructor_id_raw = driver_raw.get('Team', {}).get('_constructorId', '')
        
        # Try to get canonical name from lineup
        driver_info = get_driver_by_name(current_name, year)
        driver_full = get_driver_full_info(current_name)  # NEW: Get full info including Nationality
        
        if driver_info:
            canonical_name = driver_info['Name']
            # Get team from lineup (more authoritative than driver_block's old mapping)
            team_unique_from_lineup = driver_info.get('Team')
            # Get nationality from drivers.json if available
            driver_nationality_from_json = driver_full.get('Nationality') if driver_full else None
            log.debug(f"Driver matched: {canonical_name}")
        else:
            canonical_name = current_name
            team_unique_from_lineup = None
            driver_nationality_from_json = driver_full.get('Nationality') if driver_full else None
            log.warning(f"Driver not in lineup: {canonical_name} (using preprocessed data)")
        
        # Get nationality: prefer raw data, fallback to drivers.json
        if nationality_raw:
            nation_info = get_driver_nation(nationality_raw)
            log.debug(f"Nationality mapped: {nationality_raw} → {nation_info['Name']}")
        elif driver_nationality_from_json:
            nation_info = get_driver_nation(driver_nationality_from_json)
            log.debug(f"Nationality from drivers.json: {driver_nationality_from_json} → {nation_info['Name']}")
        else:
            nation_info = {"Name": "Unknown", "Code": "UNK"}
            log.warning(f"No nationality data for {canonical_name}")
        
        # Team info - prefer constructorId (most authoritative)
        if constructor_id_raw:
            team_info = get_team_name({"constructorId": constructor_id_raw}, year)
            log.debug(f"Team from constructorId: {constructor_id_raw} → {team_info['Name']}")
        elif team_unique_from_lineup:
            # Fallback: Extract team name from lineup uniqueName (e.g., "mclaren.2025" → "mclaren")
            team_id = team_unique_from_lineup.rsplit('.', 1)[0] if '.' in team_unique_from_lineup else team_unique_from_lineup
            team_info = get_team_name({"name": team_id}, year)
            log.debug(f"Team from lineup uniqueName: {team_unique_from_lineup} → {team_info['Name']}")
        else:
            # Last resort: validate existing team name (handle both formats)
            team_raw = driver_raw.get('Team', {})
            team_name = team_raw.get('Name') or driver_raw.get('TeamName', 'Unknown Team')
            team_info = get_team_name({"name": team_name}, year)
        
        # Clean up internal fields and update with enriched data
        if '_nationality_raw' in driver_raw['Driver']:
            del driver_raw['Driver']['_nationality_raw']
        if '_constructorId' in driver_raw.get('Team', {}):
            del driver_raw['Team']['_constructorId']
        
        driver_raw['Driver']['Name'] = canonical_name
        driver_raw['Driver']['Nationality'] = nation_info['Name']
        driver_raw['Team']['Name'] = team_info['Name']
        driver_raw['Team']['UniqueName'] = team_info['UniqueName']
        
        #  CRITICAL: Rename FastF1 fields to RLT Admin-Spec names
        # FastF1 uses different field names than RLT expects
        if 'DriverNumber' in driver_raw:
            driver_raw['RaceNumber'] = int(driver_raw.pop('DriverNumber') or 0)
        if 'Abbreviation' in driver_raw:
            driver_raw.pop('Abbreviation')  # RLT doesn't use this
        if 'TeamName' in driver_raw:
            driver_raw.pop('TeamName')  # Already have Team.Name
        
        #  CRITICAL: Remove fields NOT in Admin-Spec
        # Time and FastestLapTime are NOT in spec - only TimeInt and FastestLapTimeInt
        if 'Time' in driver_raw:
            driver_raw.pop('Time')
        if 'FastestLapTime' in driver_raw:
            driver_raw.pop('FastestLapTime')
        
        # 🔧 QUALIFYING FIX: Store raw Q times temporarily (will be used for TimeInt calculation)
        q1_raw = driver_raw.pop('Q1', None)
        q2_raw = driver_raw.pop('Q2', None)
        q3_raw = driver_raw.pop('Q3', None)
        
        # Save in temporary fields for later use
        if q1_raw:
            driver_raw['_q1_raw'] = q1_raw
        if q2_raw:
            driver_raw['_q2_raw'] = q2_raw
        if q3_raw:
            driver_raw['_q3_raw'] = q3_raw
        
        # CRITICAL: Remove FastF1 nested Driver fields (givenName, familyName)
        # RLT expects ONLY {Name, Nationality} in Driver object
        if 'givenName' in driver_raw.get('Driver', {}):
            driver_raw['Driver'].pop('givenName')
        if 'familyName' in driver_raw.get('Driver', {}):
            driver_raw['Driver'].pop('familyName')
        
        #  CRITICAL: Add missing RLT required fields with defaults
        driver_raw.setdefault('NationalityIngame', nation_info.get('Code', 'UNK'))
        driver_raw.setdefault('SeatType', 'Primary')  # Must be string, not null
        driver_raw.setdefault('Car', {"Name": "", "UniqueName": ""})  # FastF1 doesn't provide car data
        driver_raw.setdefault('StintsRaw', "")  # Would need detailed stint data
        driver_raw.setdefault('FastestLapTyres', "Soft")  # Default, FastF1 doesn't provide
        driver_raw.setdefault('FastestLapNumLap', 0)
        driver_raw.setdefault('FastestLapValidFlags', 0)
        driver_raw.setdefault('PenaltySecsIngame', 0)
        driver_raw.setdefault('PenaltyPosIngame', 0)
        driver_raw.setdefault('PenaltySecsStewards', 0)
        driver_raw.setdefault('PenaltyPosStewards', 0)
        driver_raw.setdefault('PenaltyPoints', 0)
        driver_raw.setdefault('DriverPointsRaw', 0)
        driver_raw.setdefault('TeamPointsRaw', 0)
        
        # CRITICAL FIX: For Qualification, force Status="Ok" and format Q times
        if session_type == "Qualification":
            # Admin-Spec: Quali sessions should have Status="Ok" (not "Dnf")
            driver_raw['Status'] = "Ok"
            
            # Retrieve raw Q times from temporary fields
            q1_raw = driver_raw.pop('_q1_raw', None)
            q2_raw = driver_raw.pop('_q2_raw', None)
            q3_raw = driver_raw.pop('_q3_raw', None)
            
            # Format Q1/Q2/Q3 AND calculate TimeInt
            # If current_q_session is set (FastF1 split mode), only use that session's time
            q1_ms = _to_milliseconds(q1_raw) if q1_raw else 0
            q2_ms = _to_milliseconds(q2_raw) if q2_raw else 0
            q3_ms = _to_milliseconds(q3_raw) if q3_raw else 0
            
            # 🔥 CRITICAL: Set TimeInt based on current Q session (for split mode)
            if current_q_session == 'Q1':
                driver_raw['TimeInt'] = q1_ms
                driver_raw['FastestLapTimeInt'] = q1_ms  # Must match TimeInt
                # RLT stores NO Q fields - remove them
                driver_raw.pop('Q1', None)
                driver_raw.pop('Q2', None)
                driver_raw.pop('Q3', None)
            elif current_q_session == 'Q2':
                driver_raw['TimeInt'] = q2_ms
                driver_raw['FastestLapTimeInt'] = q2_ms  # Must match TimeInt
                # RLT stores NO Q fields - remove them
                driver_raw.pop('Q1', None)
                driver_raw.pop('Q2', None)
                driver_raw.pop('Q3', None)
            elif current_q_session == 'Q3':
                driver_raw['TimeInt'] = q3_ms
                driver_raw['FastestLapTimeInt'] = q3_ms  # Must match TimeInt
                # RLT stores NO Q fields - remove them
                driver_raw.pop('Q1', None)
                driver_raw.pop('Q2', None)
                driver_raw.pop('Q3', None)
            else:
                # No split mode: use best time and keep all Q fields
                best_time_ms = 0
                for t in [q1_ms, q2_ms, q3_ms]:
                    if t > 0:
                        if best_time_ms == 0:
                            best_time_ms = t
                        else:
                            best_time_ms = min(best_time_ms, t)
                driver_raw['TimeInt'] = best_time_ms
                
                # Format all Q times (for display in combined mode)
                if q1_ms > 0:
                    driver_raw['Q1'] = format_ms_short(q1_ms)
                else:
                    driver_raw['Q1'] = "0:00.000"  # MANDATORY
                
                if q2_ms > 0:
                    driver_raw['Q2'] = format_ms_short(q2_ms)
                
                if q3_ms > 0:
                    driver_raw['Q3'] = format_ms_short(q3_ms)
        
        # Ensure TimeInt and FastestLapTimeInt are populated (not 0 if data exists)
        if 'TimeInt' not in driver_raw or driver_raw['TimeInt'] == 0:
            # Fallback to FastestLapTimeInt if TimeInt missing
            driver_raw['TimeInt'] = driver_raw.get('FastestLapTimeInt', 0)
        
        if 'FastestLapTimeInt' not in driver_raw or driver_raw['FastestLapTimeInt'] == 0:
            # Fallback to TimeInt if FastestLapTimeInt missing
            driver_raw['FastestLapTimeInt'] = driver_raw.get('TimeInt', 0)
        
        # CRITICAL: Rebuild driver dict in EXACT ORDER matching WORKING RLT files
        # NOT Admin-Spec! Working files have minimal fields and InGameName (not Nationality)
        driver = {
            "Driver": {
                "Name": canonical_name,
                "InGameName": canonical_name  # CRITICAL: RLT expects InGameName, not Nationality!
            },
            "RaceNumber": int(driver_number or 0),
            "Position": int(driver_raw.get('Position', 0)),
            "Team": {
                "Name": team_info['Name'],
                "UniqueName": team_info['UniqueName']
            },
            "SeatType": driver_raw.get('SeatType', 'Primary'),
            "Status": _map_driver_status(driver_raw.get('Status', 'Ok')),  # CRITICAL: Map to RLT enum!
            "TimeInt": driver_raw.get('TimeInt', 0),
            "GapInt": driver_raw.get('GapInt', 0),
            "FastestLapTimeInt": driver_raw.get('FastestLapTimeInt', 0),
            "FastestLapNumLap": driver_raw.get('FastestLapNumLap', 0),
            "FastestLapValidFlags": driver_raw.get('FastestLapValidFlags', 0),
            "PenaltySecsIngame": driver_raw.get('PenaltySecsIngame', 0),
            "PenaltyPosIngame": driver_raw.get('PenaltyPosIngame', 0),
            "PenaltySecsStewards": driver_raw.get('PenaltySecsStewards', 0),
            "PenaltyPosStewards": driver_raw.get('PenaltyPosStewards', 0),
            "PenaltyPoints": driver_raw.get('PenaltyPoints', 0),
            "DriverPointsRaw": driver_raw.get('DriverPointsRaw', 0),
            "TeamPointsRaw": driver_raw.get('TeamPointsRaw', 0),
            "LapsCount": driver_raw.get('LapsCount', 0),
            "GridPosition": int(driver_raw.get('GridPosition') or driver_raw.get('Position') or 0),
            "PitsCount": driver_raw.get('PitsCount', 0)
        }
        
        # Handle Qualification-specific fields
        if session_type == "Qualification":
            driver['Status'] = "Ok"
            if 'Q1' in driver_raw:
                driver['Q1'] = driver_raw['Q1']
            if 'Q2' in driver_raw:
                driver['Q2'] = driver_raw['Q2']
            if 'Q3' in driver_raw:
                driver['Q3'] = driver_raw['Q3']
        
        return driver
    
    # Legacy: Handle raw Jolpica format (if ever passed directly)
    # This path is kept for future direct Jolpica integration
    position = driver_raw.get('position') or driver_raw.get('Position')
    if not position:
        log.error(f"Driver missing position: {driver_raw}")
        return None
    
    try:
        position = int(position)
    except (ValueError, TypeError):
        log.error(f"Invalid position value: {position}")
        return None
    
    # Driver lookup (for canonical name only - number/code/nationality from raw)
    year = 2025  # TODO: extract from payload/session
    driver_info = None
    
    # Try name lookup for canonical name
    name_candidates = [
        driver_raw.get('name'),
        driver_raw.get('Name'),
        f"{driver_raw.get('FirstName', '')} {driver_raw.get('LastName', '')}".strip(),  # Jolpica provider format
        f"{driver_raw.get('Driver', {}).get('givenName', '')} {driver_raw.get('Driver', {}).get('familyName', '')}".strip()
    ]
    
    for name_candidate in name_candidates:
        if name_candidate:
            driver_info = get_driver_by_name(name_candidate, year)
            if driver_info:
                break
    
    # Use canonical name if found, else raw
    if driver_info:
        driver_name = driver_info['Name']
        log.debug(f"Driver matched: {driver_name}")
    else:
        driver_name = name_candidates[0] or name_candidates[1] or name_candidates[2] or "Unknown Driver"
        log.warning(f"Driver not in lineup: {driver_name} (using raw data)")
    
    # Get full driver info for RaceNumber (from drivers.json - more accurate than Ergast permanentNumber)
    driver_full = get_driver_full_info(driver_name)
    
    # Number: Prefer drivers.json RaceNumber > raw data (Ergast permanentNumber is often outdated)
    if driver_full and driver_full.get('RaceNumber'):
        driver_number = driver_full['RaceNumber']
    else:
        driver_number = driver_raw.get('number') or driver_raw.get('DriverNumber') or driver_raw.get('RaceNumber')
        # Convert to int if string
        try:
            driver_number = int(driver_number) if driver_number else 0
        except (ValueError, TypeError):
            driver_number = 0
    
    driver_code = driver_raw.get('code') or driver_raw.get('Abbreviation') or driver_raw.get('Code')
    nationality_raw = driver_raw.get('nationality') or driver_raw.get('Nationality')
    
    # Team lookup from Constructor.constructorId (Jolpica format)
    constructor_dict = driver_raw.get('Constructor', {})
    constructor_id = constructor_dict.get('constructorId')
    
    if constructor_id:
        # Use constructor ID from Jolpica
        team_info = get_team_name({"constructorId": constructor_id}, year)
    else:
        team_info = {"Name": "Unknown Team", "UniqueName": "Unknown", "Abbr": "UNK"}
    
    # Nation lookup
    nation_info = get_driver_nation(nationality_raw) if nationality_raw else {"Name": "Unknown", "Code": "UNK"}
    
    # Times (convert to int milliseconds)
    time_str = driver_raw.get('time') or driver_raw.get('Time') or ""
    
    log.debug(f"[TIME DEBUG] Driver {driver_raw.get('Position')}: time_str='{time_str}', has _q3_raw={bool(driver_raw.get('_q3_raw'))}")
    
    # 🔧 QUALIFYING FIX: If Time is empty, use best Q time (Q3 > Q2 > Q1) from RAW data
    if not time_str:
        q3_raw = driver_raw.get('_q3_raw') or ""
        q2_raw = driver_raw.get('_q2_raw') or ""
        q1_raw = driver_raw.get('_q1_raw') or ""
        time_str = q3_raw or q2_raw or q1_raw  # Best available time (raw format)
        if time_str:
            log.debug(f"Using Q-time for driver: q3={q3_raw}, q2={q2_raw}, q1={q1_raw} → time_str='{time_str}'")
    
    leader_time_str = driver_raw.get('LeaderTime') or ""
    
    # For P2+, Time is gap string (e.g., "+22.457")
    # We need to calculate total time = leader_time + gap
    if time_str.startswith('+') and leader_time_str:
        leader_time_ms = _to_milliseconds(leader_time_str)
        gap_seconds = _to_milliseconds(time_str.lstrip('+'))  # Parse gap as seconds
        time_int = leader_time_ms + gap_seconds
    else:
        # P1 or no leader time available
        time_int = _to_milliseconds(time_str)
    
    gap_int = 0  # Will be calculated later
    fastest_lap_time = _to_milliseconds(
        driver_raw.get('fastest_lap_time') or driver_raw.get('FastestLapTime')
    )
    
    # Laps
    laps = driver_raw.get('laps') or driver_raw.get('Laps') or 0
    try:
        laps = int(laps)
    except (ValueError, TypeError):
        laps = 0
    
    # Stints
    stints_raw_list = driver_raw.get('stints') or driver_raw.get('Stints') or []
    stints_raw_str = encode_stints_raw(stints_raw_list)
    
    # Status (map to RLT enum)
    status = _map_driver_status(driver_raw.get('status') or driver_raw.get('Status'))
    
    # Optional fields
    seat_type = _map_seat_type(driver_raw.get('seat_type'))
    
    # Build RLT-compliant driver object in EXACT ORDER matching WORKING files
    # CRITICAL: Use InGameName (not Nationality), minimal fields only
    driver = {
        "Driver": {
            "Name": driver_name,
            "InGameName": driver_name  # CRITICAL: RLT expects InGameName!
        },
        "RaceNumber": driver_number if driver_number is not None else 0,
        "Position": position,
        "Team": {
            "Name": team_info['Name'],
            "UniqueName": team_info['UniqueName']
        },
        "SeatType": seat_type or "Primary",
        "Status": status,
        "TimeInt": time_int,
        "GapInt": gap_int,
        "FastestLapTimeInt": fastest_lap_time,
        "FastestLapNumLap": 0,
        "FastestLapValidFlags": 0,
        "PenaltySecsIngame": 0,
        "PenaltyPosIngame": 0,
        "PenaltySecsStewards": 0,
        "PenaltyPosStewards": 0,
        "PenaltyPoints": 0,
        "DriverPointsRaw": 0,
        "TeamPointsRaw": 0,
        "LapsCount": laps,
        "GridPosition": int(driver_raw.get('grid_position') or driver_raw.get('GridPosition') or position),
        "PitsCount": driver_raw.get('pits') or driver_raw.get('PitsCount') or 0
    }
    
    # CRITICAL FIX: For Qualification, force Status="Ok" and add Q1/Q2/Q3 fields
    if session_type == "Qualification":
        driver['Status'] = "Ok"
        
        # Q1/Q2/Q3 from raw data (already formatted strings like "0 days 00:01:29.179000")
        q1_raw = driver_raw.get('Q1') or ""
        q2_raw = driver_raw.get('Q2') or ""
        q3_raw = driver_raw.get('Q3') or ""
        
        # Parse and format Q times
        q1_ms = _to_milliseconds(q1_raw)
        q2_ms = _to_milliseconds(q2_raw)
        q3_ms = _to_milliseconds(q3_raw)
        
        # Q1 is MANDATORY (use best time as fallback)
        if q1_ms > 0:
            driver['Q1'] = format_ms_short(q1_ms)
        elif driver.get('TimeInt', 0) > 0:
            driver['Q1'] = format_ms_short(driver['TimeInt'])
        else:
            driver['Q1'] = "0:00.000"
        
        # Q2 and Q3 are optional
        if q2_ms > 0:
            driver['Q2'] = format_ms_short(q2_ms)
        if q3_ms > 0:
            driver['Q3'] = format_ms_short(q3_ms)
    
    # Ensure TimeInt and FastestLapTimeInt are populated
    if driver['TimeInt'] == 0 and driver.get('FastestLapTimeInt', 0) > 0:
        driver['TimeInt'] = driver['FastestLapTimeInt']
    
    if driver.get('FastestLapTimeInt', 0) == 0 and driver['TimeInt'] > 0:
        driver['FastestLapTimeInt'] = driver['TimeInt']
    
    return driver


def encode_stints_raw(stints: list[dict]) -> str:
    """Encode stints to RLT StintsRaw format.
    
    Format: tyre_type:laps:wear_start:wear_end[,...]
    - tyre_type: Numeric from TYRE_TYPE_TO_NUM (0-22)
    - laps: Number of laps on this tyre
    - wear_start: Tyre wear at start (optional, empty if unknown)
    - wear_end: Tyre wear at end (optional, empty if unknown)
    
    Args:
        stints: List of stint dicts with keys:
                - tyre_type (str or int)
                - laps (int)
                - wear_start (optional int)
                - wear_end (optional int)
    
    Returns:
        StintsRaw string (empty if no stints)
    """
    if not stints:
        return ""
    
    encoded_stints = []
    
    for stint in stints:
        # Tyre type (convert to numeric)
        tyre_type = stint.get('tyre_type')
        if tyre_type is None:
            tyre_type = stint.get('TyreType')
        
        if isinstance(tyre_type, str):
            tyre_num = TYRE_TYPE_TO_NUM.get(tyre_type)
            if tyre_num is None:
                log.warning(f"Unknown tyre type in stint: {tyre_type}")
                continue
        elif isinstance(tyre_type, int):
            tyre_num = tyre_type
        else:
            log.warning(f"Invalid tyre type in stint: {tyre_type}")
            continue
        
        # Laps
        laps = stint.get('laps')
        if laps is None:
            laps = stint.get('Laps')
        if laps is None:
            laps = 0
        try:
            laps = int(laps)
        except (ValueError, TypeError):
            laps = 0
        
        # Wear (optional)
        wear_start = stint.get('wear_start')
        if wear_start is None:
            wear_start = stint.get('WearStart')
        wear_end = stint.get('wear_end')
        if wear_end is None:
            wear_end = stint.get('WearEnd')
        
        wear_start_str = str(int(wear_start)) if wear_start is not None else ""
        wear_end_str = str(int(wear_end)) if wear_end is not None else ""
        
        # Encode: tyre:laps:wear_start:wear_end
        encoded = f"{tyre_num}:{laps}:{wear_start_str}:{wear_end_str}"
        encoded_stints.append(encoded)
    
    return ",".join(encoded_stints)


def _calculate_gaps_race(drivers: list[dict]) -> list[dict]:
    """Calculate Race gaps (GapInt = time behind leader).
    
    Race gap logic:
    - Leader (Position=1): GapInt=0
    - Same lap as leader: GapInt = driver_time - leader_time (milliseconds behind)
    - Lapped drivers: GapInt=0
    - DNF/DSQ: GapInt=0
    
    CRITICAL VALIDATION:
    - For Position > 1, GapInt must NOT equal FastestLapTimeInt (±2ms tolerance)
    - This catches bugs where gaps are incorrectly set to lap times
    
    Args:
        drivers: List of driver dicts (sorted by Position)
        
    Returns:
        Updated drivers with GapInt calculated
    """
    if not drivers:
        return drivers
    
    # Sort by Position
    drivers_sorted = sorted(drivers, key=lambda d: d.get('Position', 999))
    
    # Find leader
    leader = drivers_sorted[0]
    leader_time = leader.get('TimeInt', 0)
    leader_laps = leader.get('Laps', 0)
    
    # Set leader gap to 0
    leader['GapInt'] = 0
    
    for driver in drivers_sorted[1:]:
        driver_time = driver.get('TimeInt', 0)
        driver_laps = driver.get('Laps', 0)
        
        # Check if same lap as leader
        if driver_laps == leader_laps and driver_time > 0 and leader_time > 0:
            gap = driver_time - leader_time
            driver['GapInt'] = max(0, gap)  # Never negative
        else:
            # Lapped or DNF
            driver['GapInt'] = 0
        
        # VALIDATION: Gap should NOT equal fastest lap time
        _validate_gap_not_lap_time(driver)
    
    return drivers_sorted


def _calculate_gaps_quali(drivers: list[dict]) -> list[dict]:
    """Calculate Qualification/Practice gaps (GapInt = time behind pole).
    
    Quali gap logic:
    - Pole (Position=1): GapInt=0
    - All others: GapInt = driver_best_lap - pole_best_lap (always >= 0)
    - No lap time: GapInt=0
    
    Args:
        drivers: List of driver dicts (sorted by Position)
        
    Returns:
        Updated drivers with GapInt calculated
    """
    if not drivers:
        return drivers
    
    # Sort by Position
    drivers_sorted = sorted(drivers, key=lambda d: d.get('Position', 999))
    
    # Find pole time
    pole = drivers_sorted[0]
    pole_time = pole.get('FastestLapTimeInt') or pole.get('TimeInt') or 0
    
    # Set pole gap to 0
    pole['GapInt'] = 0
    
    for driver in drivers_sorted[1:]:
        driver_time = driver.get('FastestLapTimeInt') or driver.get('TimeInt') or 0
        
        if driver_time > 0 and pole_time > 0:
            gap = driver_time - pole_time
            driver['GapInt'] = max(0, gap)  # Never negative
        else:
            driver['GapInt'] = 0
    
    return drivers_sorted


def _validate_gap_not_lap_time(driver: dict) -> None:
    """Validate that GapInt is not mistakenly set to lap time.
    
    Common bug: GapInt = FastestLapTimeInt (should be time behind leader).
    This validation catches that bug.
    
    Args:
        driver: Driver dict
        
    Raises:
        AssertionError: If GapInt equals FastestLapTimeInt (within 2ms tolerance)
    """
    gap = driver.get('GapInt', 0)
    lap_time = driver.get('FastestLapTimeInt', 0)
    position = driver.get('Position', 0)
    
    if position > 1 and gap > 0 and lap_time > 0:
        # Check if gap equals lap time (within 2ms tolerance)
        if abs(gap - lap_time) <= 2:
            driver_name = driver.get('Driver', {}).get('Name', driver.get('Name', 'Unknown'))
            msg = (
                f"CRITICAL BUG: Driver at position {position} has GapInt={gap} "
                f"equal to FastestLapTimeInt={lap_time}. "
                f"GapInt should be time behind leader, not lap time!"
            )
            log.error(f"{msg} [driver={driver_name}, position={position}, gap={gap}, lap_time={lap_time}]")
            raise AssertionError(msg)


def _validate_required_fields(result: dict) -> None:
    """Validate that all required fields are present per Admin-Spec.
    
    Args:
        result: RLT session dict
        
    Raises:
        ValueError: If required fields missing
    """
    session_type = result.get('SessionType')
    
    # Top-level required
    missing_top = []
    for field in TOP_LEVEL_REQUIRED:
        if field not in result:
            missing_top.append(field)
    
    if missing_top:
        raise ValueError(f"Missing required top-level fields: {', '.join(missing_top)}")
    
    # Driver required (check first driver as sample)
    drivers = result.get('Drivers', [])
    if drivers:
        # 🔥 CRITICAL: For Q1/Q2/Q3 split mode, DON'T require Q1 field (RLT stores NO Q fields)
        qual_type = result.get('QualType')
        is_split_mode = qual_type in ['Q1', 'Q2', 'Q3']
        
        if session_type == "Qualification" and not is_split_mode:
            driver_required = DRIVER_REQUIRED_QUALI  # Combined mode: Q1 required
        else:
            driver_required = DRIVER_REQUIRED  # Split mode or Race: NO Q fields
        
        missing_driver = []
        for field in driver_required:
            if field not in drivers[0]:
                missing_driver.append(field)
        
        if missing_driver:
            raise ValueError(f"Missing required driver fields: {', '.join(missing_driver)}")
        
        # For qualification, verify Q1 field exists ONLY if NOT split mode
        # Split mode (Q1/Q2/Q3 separate files) has NO Q fields per RLT spec
        if session_type == "Qualification":
            qual_type = result.get('QualType')
            is_split_mode = qual_type in ['Q1', 'Q2', 'Q3']
            
            if not is_split_mode:
                # Combined qualifying mode - Q1 field is MANDATORY
                for i, driver in enumerate(drivers, 1):
                    if 'Q1' not in driver:
                        raise ValueError(f"Driver at position {i} missing Q1 field (MANDATORY for combined qualification)")
                    # Verify format "m:ss.mmm"
                    q1 = driver['Q1']
                    if not isinstance(q1, str) or ':' not in q1:
                        raise ValueError(f"Driver at position {i} has invalid Q1 format: {q1} (expected 'm:ss.mmm')")
            # else: Split mode - NO Q fields expected (RLT uses TimeInt only)
            
            # Verify Status="Ok" for all quali sessions
            for i, driver in enumerate(drivers, 1):
                if driver.get('Status') != "Ok":
                    log.warning(f"Driver at position {i} has Status='{driver.get('Status')}' (should be 'Ok' for qualification)")


def _to_milliseconds(value: Any) -> int:
    """Convert time value to integer milliseconds.
    
    Args:
        value: Can be int (ms), float (seconds), str (various formats), or None
        
    Returns:
        Time in integer milliseconds (0 if None or invalid)
    """
    if value is None:
        return 0
    
    # Already in milliseconds (int)
    if isinstance(value, int):
        return max(0, value)
    
    # Seconds (float)
    if isinstance(value, float):
        return max(0, int(value * 1000))
    
    # String parsing
    if isinstance(value, str):
        value = value.strip()
        
        # Empty string
        if not value or value in ['DNF', 'DSQ', 'DNS']:
            return 0
        
        # 🔧 FASTF1 TIMEDELTA FORMAT: "0 days 00:01:30.031000"
        if 'days' in value:
            try:
                # Split on "days"
                parts = value.split('days')
                days = int(parts[0].strip())
                time_part = parts[1].strip()  # "00:01:30.031000"
                
                # Parse HH:MM:SS.ffffff
                time_parts = time_part.split(':')
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                seconds = float(time_parts[2])
                
                total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
                return max(0, int(total_seconds * 1000))
            except (ValueError, IndexError) as e:
                log.warning(f"Failed to parse timedelta format '{value}': {e}")
                return 0
        
        # Try as float seconds
        try:
            seconds = float(value)
            return max(0, int(seconds * 1000))
        except ValueError:
            pass
        
        # Try H:MM:SS.mmm or MM:SS.mmm format
        if ':' in value:
            try:
                parts = value.split(':')
                if len(parts) == 3:
                    # H:MM:SS.mmm format (race total time)
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    return max(0, int((hours * 3600 + minutes * 60 + seconds) * 1000))
                elif len(parts) == 2:
                    # MM:SS.mmm format (lap time)
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return max(0, int((minutes * 60 + seconds) * 1000))
            except (ValueError, IndexError):
                pass
        
        log.warning(f"Unable to parse time string: {value}")
        return 0
    
    log.warning(f"Unsupported time value type: {type(value).__name__}")
    return 0


# Enum mappers
def _map_session_type(value: Any) -> str:
    """Map session type to RLT enum."""
    if not value:
        return "Race"
    
    value_str = str(value).lower()
    if 'race' in value_str:
        return "Race"
    elif 'qual' in value_str:
        return "Qualification"
    elif 'practice' in value_str or 'fp' in value_str:
        return "Practice"
    else:
        log.warning(f"Unknown session type: {value}")
        return "Race"


def _map_race_type(value: Any) -> str:
    """Map race type to RLT enum (required field)."""
    if not value:
        return "Main"  # Default (matching working RLT files)
    
    value_str = str(value).lower()
    if 'sprint' in value_str:
        return "Sprint"
    elif 'feature' in value_str:
        return "Feature"
    elif 'main' in value_str:
        return "Main"
    elif 'first' in value_str or '1' in value_str:
        return "First"
    elif 'second' in value_str or '2' in value_str:
        return "Second"
    elif 'third' in value_str or '3' in value_str:
        return "Third"
    else:
        return "Main"  # Changed from "Regular"


def _map_qual_type(value: Any) -> str:
    """Map qualification type to RLT enum."""
    if not value:
        return "Regular"  # Default
    
    value_str = str(value).lower()
    if 'q1' in value_str:
        return "Q1"
    elif 'q2' in value_str:
        return "Q2"
    elif 'q3' in value_str:
        return "Q3"
    elif 'q4' in value_str:
        return "Q4"
    else:
        return "Regular"


def _map_weather(value: Any) -> str | None:
    """Map weather to RLT enum."""
    if not value:
        return None
    
    value_str = str(value).lower()
    if 'storm' in value_str:
        return "Storm"
    elif 'heavy' in value_str and 'rain' in value_str:
        return "HeavyRain"
    elif 'light' in value_str and 'rain' in value_str:
        return "LightRain"
    elif 'rain' in value_str or 'wet' in value_str:
        return "LightRain"
    elif 'overcast' in value_str:
        return "Overcast"
    elif 'light' in value_str and 'cloud' in value_str:
        return "LightCloud"
    elif 'cloud' in value_str:
        return "LightCloud"
    elif 'clear' in value_str or 'sunny' in value_str:
        return "Clear"
    else:
        return None


def _map_driver_status(value: Any) -> str:
    """Map driver status to RLT enum (Ok, Dns, Dnf, Dsq)."""
    if not value:
        return "Ok"
    
    value_str = str(value).lower()
    
    # Map to exact RLT Status enum values
    if 'dnf' in value_str or 'retired' in value_str or 'ret' in value_str:
        return "Dnf"
    elif 'dsq' in value_str or 'disqualified' in value_str:
        return "Dsq"
    elif 'dns' in value_str or 'dnq' in value_str:
        return "Dns"
    elif 'finished' in value_str or 'ok' in value_str or 'fin' in value_str:
        return "Ok"
    else:
        # Default for completed status
        return "Ok"


def _map_seat_type(value: Any) -> str | None:
    """Map seat type to RLT enum."""
    if not value:
        return None
    
    value_str = str(value).lower()
    if 'reserve' in value_str:
        return "Reserve"
    elif 'test' in value_str:
        return "TestDriver"
    else:
        return None
