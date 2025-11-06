import json
import os
from datetime import datetime, timedelta
from api.jolpica_api import fetch_race_data
from utils.logging_setup import get_logger

# Initialize logger
log = get_logger(__name__)

# --- Path Correction ---
# Get the absolute path to the project's root directory
# This makes file loading independent of where the script is run from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# --- Load Mapping Files ---
try:
    with open(os.path.join(PROJECT_ROOT, "mapping", "circuits.json"), "r", encoding="utf-8") as f:
        circuits = json.load(f)
    log.info(f"Circuits mapping loaded: {len(circuits)} total")
except FileNotFoundError:
    log.error("circuits.json not found in mapping directory")
    circuits = []

try:
    DRIVERS_JSON_PATH = os.path.join(PROJECT_ROOT, "mapping", "drivers.json")
    with open(DRIVERS_JSON_PATH, "r", encoding="utf-8") as f:
        ALL_DRIVERS = json.load(f)
    DRIVER_NAME_MAP = {d["Name"]: d for d in ALL_DRIVERS}
    log.info(f"Drivers mapping loaded: {len(ALL_DRIVERS)} total")
except FileNotFoundError:
    log.error("drivers.json not found in mapping directory")
    ALL_DRIVERS = []
    DRIVER_NAME_MAP = {}

def find_circuit_by_api_name(api_name):
    api_name = api_name.lower()
    for c in circuits:
        if (
            c.get("CircuitName", "").lower() == api_name
            or c.get("CircuitFullName", "").lower() == api_name
            or c.get("UniqueName", "").lower() == api_name
            or any(alias.lower() == api_name for alias in c.get("Aliases", []))
        ):
            return c
    return None

def build_session_metadata(year, round_number, session_type="results"):
    log.debug(f"Building session metadata: year={year}, round={round_number}, session_type={session_type}")
    data = fetch_race_data(year, round_number, session_type)
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    if not races:
        log.warning(f"No race data found: year={year}, round={round_number}, session_type={session_type}")
        return {}
    race_data = races[0]

    # Ergebnis-Block dynamisch wählen
    results = []
    if session_type.lower() == "sprint" and "SprintResults" in race_data:
        results = race_data["SprintResults"]
    elif session_type.lower() == "qualifying" and "QualifyingResults" in race_data:
        results = race_data["QualifyingResults"]
    elif "Results" in race_data:
        results = race_data["Results"]

    if not results:
        log.warning(f"No results block found: year={year}, round={round_number}, session_type={session_type}")
        return {}

    # Runde = SessionPosition
    session_position = int(race_data.get("round", 0))

    # Fastest Lap Info
    if results:
        fastest_driver = results[0].get("Driver")
    else:
        fastest_driver = None

    fastest_driver_name = get_driver_name(f"{fastest_driver['givenName']} {fastest_driver['familyName']}") if fastest_driver else "Unbekannt"
    fastest_lap_data = results[0].get("FastestLap", {}) if results else {}
    fastest_lap_time_str = fastest_lap_data.get("Time", {}).get("time", "0:00.000")
    fastest_lap_time_int = int(fastest_lap_time_str.replace(":", "").replace(".", "")) if fastest_lap_time_str else 0
    fastest_lap_num = int(fastest_lap_data.get("lap", 0))

    # Datum aus API oder Fallback
    start_time = race_data.get("date", "2025-01-01") + "T19:00:00"
    end_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S") + timedelta(minutes=90)

    circuit_api_name = race_data["Circuit"]["circuitName"]
    circuit = find_circuit_by_api_name(circuit_api_name)
    track_name = circuit["CircuitName"] if circuit else circuit_api_name
    track_unique = circuit["UniqueName"] if circuit else "unknown.track"

    metadata = {
        "SessionType": session_type.capitalize(),
        "RaceType": "Regular",
        "QualType": "Regular",
        "SessionStatus": "FullPoints",
        "SessionPosition": session_position,
        "FastestLapTimeInt": fastest_lap_time_int,
        "FastestLapNumLap": fastest_lap_num,
        "TrackName": track_name,
        "TrackUniqueName": track_unique,
        "IsLiveData": False,
        "LiveRecordPercent": 0,
        "IsLiveFullRecord": False,
        "IsSingleplayerMode": False,
        "WeatherType": "Clear",
        "AirTemperature": 0,
        "TrackTemperature": 0,
        "TotalLaps": int(results[0].get("laps", 0)) if results else 0,
        "SessionDuration": "00:00:00",
    }

    return metadata



def get_driver_name(full_name: str) -> dict:
    return DRIVER_NAME_MAP.get(full_name, {
        "Name": full_name,
        "InGameName": full_name,
        "Nationality": "",
        "RaceNumber": 0,
    })

def map_driver_data(driver_data, api_driver_result=None):
    driver_block = {
        "Driver": {
            "Name": driver_data["Name"],
            "InGameName": driver_data.get("InGameName", driver_data["Name"]),
        },
        "RaceNumber": int(api_driver_result.get("number", 0)) if api_driver_result else 0,
        # ...weitere API-Felder hier ergänzen...
    }
    return driver_block

def build_driver_blocks(year, round_number, session_type="results", quali_phase=None):
    data = fetch_race_data(year, round_number, session_type)
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    if not races:
        return []
    race_data = races[0]

    # Ergebnis-Block dynamisch wählen
    results = []
    if session_type.lower() == "qualifying" and "QualifyingResults" in race_data:
        results = race_data["QualifyingResults"]
    elif session_type.lower() == "sprint" and "SprintResults" in race_data:
        results = race_data["SprintResults"]
    elif "Results" in race_data:
        results = race_data["Results"]

    driver_blocks = []
    if session_type.lower() == "qualifying" and quali_phase:
        # Nur Fahrer exportieren, die in dieser Phase gefahren sind!
        for res in results:
            quali_time_str = res.get(quali_phase, None)
            if quali_time_str is not None:  # Nur Fahrer, die in dieser Session gefahren sind
                driver_api_name = f"{res['Driver']['givenName']} {res['Driver']['familyName']}"
                driver_data = get_driver_name(driver_api_name)
                driver_block = map_driver_data(driver_data, res)
                driver_block[quali_phase] = quali_time_str
                driver_blocks.append(driver_block)
    else:
        # Rennen/Sprint: alle Fahrer wie gehabt
        for res in results:
            driver_api_name = f"{res['Driver']['givenName']} {res['Driver']['familyName']}"
            driver_data = get_driver_name(driver_api_name)
            driver_block = map_driver_data(driver_data, res)
            driver_blocks.append(driver_block)
    return driver_blocks
