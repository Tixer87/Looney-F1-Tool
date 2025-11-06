"""RLT Session Result Format Enums - Auto-generated from spec."""

from typing import Literal

SessionType = Literal["Race", "Qualification", "Practice"]

RaceType = Literal["Regular", "Main", "Sprint", "Feature", "First", "Second", "Third", "Safety", "Special"]

QualType = Literal["Regular", "Q1", "Q2", "Q3", "Q4"]

SessionStatus = Literal["FullPoints", "HalfPoints", "NoPoints"]

SeatType = Literal["Primary", "Reserve", "NoSeat"]

Status = Literal["Ok", "Dns", "Dnf", "Dsq"]

WeatherType = Literal["Clear", "LightCloud", "Overcast", "LightRain", "HeavyRain", "Storm"]

TyreType = Literal["Soft", "Medium", "Hard", "Intermediate", "Wet", "SuperSoft", "UltraSoft", "HyperSoft", "C1", "C2", "C3", "C4", "C5", "C6", "Option", "Prime", "Qualifying", "Slick", "Rain", "Snow", "Gravel", "Mud", "Sand", "AllTerrain", "SemiSlick", "Street", "StreetVintage", "AllWeather"]

# TyreType numeric values (for StintsRaw)
TYRE_TYPE_TO_NUM = {
    "Soft": 0,
    "Medium": 1,
    "Hard": 2,
    "Intermediate": 3,
    "Wet": 4,
    "SuperSoft": 5,
    "UltraSoft": 6,
    "HyperSoft": 7,
    "C1": 11,
    "C2": 12,
    "C3": 13,
    "C4": 14,
    "C5": 15,
    "C6": 16,
    "Option": 20,
    "Prime": 21,
    "Qualifying": 22,
}

TYRE_NUM_TO_TYPE = {
    0: "Soft",
    1: "Medium",
    2: "Hard",
    3: "Intermediate",
    4: "Wet",
    5: "SuperSoft",
    6: "UltraSoft",
    7: "HyperSoft",
    11: "C1",
    12: "C2",
    13: "C3",
    14: "C4",
    15: "C5",
    16: "C6",
    20: "Option",
    21: "Prime",
    22: "Qualifying",
}

# Required fields (per Admin-Spec rlt_import_session_results_json_format.txt)
# CRITICAL: Based on working RLT files, Date/FastestLapDriver/DriverDayDriver are OPTIONAL
TOP_LEVEL_REQUIRED = [
    'SessionType', 'RaceType', 'SessionStatus', 'SessionPosition',
    'FastestLapTimeInt', 'FastestLapNumLap',
    'TrackName', 'TrackUniqueName', 
    'IsLiveData', 'LiveRecordPercent', 'IsLiveFullRecord', 'IsSingleplayerMode',
    'WeatherType', 'AirTemperature', 'TrackTemperature',
    'TotalLaps', 'SessionDuration',
    'Drivers'
]

DRIVER_REQUIRED = [
    'Driver', 'Position', 'Team', 'SeatType', 'Status', 
    'TimeInt', 'GapInt', 'LapsCount', 'GridPosition', 'PitsCount'
]

# Qualification-specific required fields
DRIVER_REQUIRED_QUALI = DRIVER_REQUIRED + ['Q1']  # Q1 is MANDATORY for qualification sessions