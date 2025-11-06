from api.jolpica_api import fetch_race_data
from api.jolpica_api import fetch_pitstops_data
from core.helpers import time_as_int
from utils.logging_setup import get_logger
import json
import os

# Initialize logger
log = get_logger(__name__)

# --- Path Correction ---
# Get the absolute path to the project's root directory
# This makes file loading independent of where the script is run from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DEFAULT_FASTEST_LAP_FLAGS = 15

# --- Load Mapping Files ---
try:
    TEAMS_JSON_PATH = os.path.join(PROJECT_ROOT, "mapping", "teams.f1.json")
    with open(TEAMS_JSON_PATH, "r", encoding="utf-8") as f:
        ALL_TEAMS = json.load(f)
    TEAM_ID_MAP = {}
    for t in ALL_TEAMS:
        if "ApiId" in t:
            TEAM_ID_MAP[t["ApiId"].lower()] = t
        TEAM_ID_MAP[t["Name"].lower().replace(" ", "_")] = t
        TEAM_ID_MAP[t["UniqueName"].split(".")[0].lower()] = t
    log.info(f"Teams mapping loaded: {len(ALL_TEAMS)} total")
except FileNotFoundError:
    log.error("teams.f1.json not found in mapping directory")
    ALL_TEAMS = []
    TEAM_ID_MAP = {}

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


def get_team_data(constructor_id: str) -> dict:
    key = constructor_id.lower()
    return TEAM_ID_MAP.get(key, {
        "Name": constructor_id,
        "UniqueName": "",
        "Car": "",
        "Nationality": "",
        "Year": 0
    })

def get_driver_name(full_name: str) -> dict:
    key = full_name.strip()
    return DRIVER_NAME_MAP.get(key, {
        "Name": full_name,
        "InGameName": full_name,
    })

def parse_stints_for_driver(pitstops: list, total_laps: int):
    stints = []
    compounds = []
    prev_lap = 1

    for stop in pitstops:
        lap = int(stop["lap"])
        stint_len = lap - prev_lap
        stints.append(f"X{stint_len}")
        compounds.append("Unknown")
        prev_lap = lap

    stint_len = total_laps - prev_lap + 1
    stints.append(f"X{stint_len}")
    compounds.append("Unknown")

    return ",".join(stints), len(stints), compounds

def build_driver_block(driver_result: dict, year: int, round_number: int, winner_time_ms: int) -> dict:
    driver_api_name = f"{driver_result['Driver']['givenName']} {driver_result['Driver']['familyName']}"
    driver_data = get_driver_name(driver_api_name)
    driver_number = int(driver_result.get("number", 0))
    team_data = get_team_data(driver_result["Constructor"]["constructorId"])
    driver_team_name = team_data["Name"]
    driver_team_unique = team_data["UniqueName"]
    
    # Extract nationality from Jolpica API data
    nationality_raw = driver_result.get("Driver", {}).get("nationality", "")
    constructor_id_raw = driver_result.get("Constructor", {}).get("constructorId", "")

    seat_type = "Primary"
    status = "Ok" if driver_result.get("status", "").lower() == "finished" else "Dnf"
    total_time = driver_result.get("Time", {}).get("time", "0")
    time_int = int(driver_result.get("Time", {}).get("millis", 0))
    gap_int = time_int - winner_time_ms if time_int and winner_time_ms else 0
    fastest_lap_time = driver_result.get("FastestLap", {}).get("Time", {}).get("time", "0:00.000")
    fastest_lap_lap = int(driver_result.get("FastestLap", {}).get("lap", 0))
    fastest_lap_time_int = time_as_int(fastest_lap_time)
    fastest_lap_flags = 0
    laps_count = int(driver_result.get("laps", 0))

    pitstops_data = fetch_pitstops_data(year, round_number)
    target_driver_id = driver_result["Driver"]["driverId"].lower()
    pitstops_driver = [p for p in pitstops_data if p["driverId"].lower() == target_driver_id]

    driver_block = {
        "Driver": {
            "Name": driver_data["Name"],
            "InGameName": driver_data.get("InGameName", driver_data["Name"]),
            "_nationality_raw": nationality_raw  # Pass to adapter for nation lookup
        },
        "RaceNumber": driver_number,
        "Position": int(driver_result.get("position", 0)),
        "Team": {
            "Name": driver_team_name,
            "UniqueName": driver_team_unique,
            "_constructorId": constructor_id_raw  # Pass to adapter for team validation
        },
        "SeatType": seat_type,
        "Status": status,
        "TimeInt": time_int,
        "GapInt": gap_int,
        "FastestLapTimeInt": fastest_lap_time_int,
        "FastestLapNumLap": fastest_lap_lap,
        "FastestLapValidFlags": fastest_lap_flags,
        "PenaltySecsIngame": 0,
        "PenaltyPosIngame": 0,
        "PenaltySecsStewards": 0,
        "PenaltyPosStewards": 0,
        "PenaltyPoints": 0,
        "DriverPointsRaw": 0,
        "TeamPointsRaw": 0,
        "LapsCount": laps_count,
        "GridPosition": int(driver_result.get("grid", 0)),
        "PitsCount": len(pitstops_driver),
    }
    return driver_block

def build_driver_blocks(year, round_number, session_type="results", quali_phase=None):
    data = fetch_race_data(year, round_number, session_type)
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    if not races:
        return []
    race_data = races[0]

    if session_type.lower() == "qualifying" and "QualifyingResults" in race_data:
        results = race_data["QualifyingResults"]
    elif session_type.lower() == "sprint" and "SprintResults" in race_data:
        results = race_data["SprintResults"]
    elif "Results" in race_data:
        results = race_data["Results"]
    else:
        results = []

    driver_blocks = []
    if session_type.lower() == "qualifying" and quali_phase:
        max_pos = 15 if quali_phase == "Q2" else 10 if quali_phase == "Q3" else 20
        for res in results:
            pos = int(res.get("position", 0))
            if pos > max_pos:
                continue
            quali_time_str = res.get(quali_phase, "")
            driver_api_name = f"{res['Driver']['givenName']} {res['Driver']['familyName']}"
            driver_data = get_driver_name(driver_api_name)
            driver_number = int(res.get("number", 0))
            team_data = get_team_data(res["Constructor"]["constructorId"])
            driver_team_name = team_data["Name"]
            driver_team_unique = team_data["UniqueName"]
            
            # Extract nationality and constructorId from Jolpica API data
            nationality_raw = res.get("Driver", {}).get("nationality", "")
            constructor_id_raw = res.get("Constructor", {}).get("constructorId", "")

            seat_type = "Primary"
            status = "Ok"
            time_int = time_as_int(quali_time_str) if quali_time_str else 0
            gap_int = 0
            fastest_lap_time_int = time_as_int(quali_time_str) if quali_time_str else 0
            fastest_lap_lap = 1
            fastest_lap_flags = DEFAULT_FASTEST_LAP_FLAGS
            laps_count = 1

            driver_block = {
                "Driver": {
                    "Name": driver_data["Name"],
                    "InGameName": driver_data.get("InGameName", driver_data["Name"]),
                    "_nationality_raw": nationality_raw  # Pass to adapter for nation lookup
                },
                "RaceNumber": driver_number,
                "Position": pos,
                "Team": {
                    "Name": driver_team_name,
                    "UniqueName": driver_team_unique,
                    "_constructorId": constructor_id_raw  # Pass to adapter for team validation
                },
                "SeatType": seat_type,
                "Status": status,
                "TimeInt": time_int,
                "GapInt": gap_int,
                "FastestLapTimeInt": fastest_lap_time_int,
                "FastestLapNumLap": fastest_lap_lap,
                "FastestLapValidFlags": fastest_lap_flags,
                "PenaltySecsIngame": 0,
                "PenaltyPosIngame": 0,
                "PenaltySecsStewards": 0,
                "PenaltyPosStewards": 0,
                "PenaltyPoints": 0,
                "DriverPointsRaw": 0,
                "TeamPointsRaw": 0,
                "LapsCount": laps_count,
                "GridPosition": pos,
                "PitsCount": 0,
                quali_phase: quali_time_str if quali_time_str else ""
            }
            driver_blocks.append(driver_block)
    else:
        winner_time_ms = 0
        if results and results[0].get("Time", {}).get("millis"):
            winner_time_ms = int(results[0]["Time"]["millis"])
        for res in results:
            driver_block = build_driver_block(res, year, round_number, winner_time_ms)
            driver_blocks.append(driver_block)
    return driver_blocks