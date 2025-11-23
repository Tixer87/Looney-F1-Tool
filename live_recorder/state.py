"""
Data Classes für Live Session State
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone


@dataclass
class WeatherData:
    """Wetterdaten"""
    air_temp: str              # Celsius
    track_temp: str
    humidity: str              # Prozent
    rainfall: bool             # True wenn Regen
    wind_speed: str            # km/h
    wind_direction: str        # Grad


@dataclass
class RaceControlEvent:
    """Race Control Message"""
    timestamp: datetime        # UTC
    lap: int
    category: str              # "SafetyCar", "Flag", "Drs", "Other"
    message: str               # Original Message Text
    flag: Optional[str] = None # "YELLOW", "RED", "GREEN", etc.
    scope: Optional[str] = None # "Track", "Driver", "Sector"
    driver_number: Optional[str] = None  # Falls fahrer-spezifisch


@dataclass
class LapData:
    """Lap Timing"""
    lap_number: int
    laptime: Optional[str]
    sector_1: Optional[str]
    sector_2: Optional[str]
    sector_3: Optional[str]
    position: int
    gap_to_leader: str


@dataclass
class StintData:
    """Ein Reifenstint"""
    stint_number: int
    compound: str              # "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
    is_new: bool               # True wenn neuer Reifen
    start_lap: Optional[int] = None
    end_lap: Optional[int] = None
    total_laps: int = 0


@dataclass
class PitstopData:
    """Ein Boxenstopp"""
    stop_number: int
    lap: int                   # Runde des Stops
    compound_in: str           # Alter Reifen
    compound_out: str          # Neuer Reifen
    duration_estimate: Optional[float] = None  # Sekunden (geschätzt)


@dataclass
class LiveDriverState:
    """State pro Fahrer während Live Recording"""
    
    # Identity
    racing_number: str
    tla: str                   # "VER"
    full_name: str             # "Max Verstappen"
    broadcast_name: str
    first_name: str
    last_name: str
    
    # Team
    team_name: str             # "Red Bull Racing"
    team_colour: str           # Hex ohne #
    
    # Nation
    country_code: str          # "NED"
    
    # Positions
    grid_position: int = 0     # Startposition
    current_position: int = 0
    final_position: Optional[int] = None
    
    # Timing
    laps_completed: int = 0
    best_laptime: Optional[str] = None          # "1:20.123"
    last_laptime: Optional[str] = None
    best_sectors: List[Optional[str]] = field(default_factory=lambda: [None, None, None])
    
    # Status Flags
    in_pit: bool = False
    pit_out: bool = False
    retired: bool = False
    stopped: bool = False
    knocked_out: bool = False  # Qualifying
    
    # Finishing Status
    finishing_status: str = "Running"  # "Running", "Finished", "DNF", "DNS", "DSQ"
    
    # Stints & Pitstops
    stints: List[StintData] = field(default_factory=list)
    pitstops: List[PitstopData] = field(default_factory=list)
    
    # Lap History (optional, für Analytics)
    lap_history: List[LapData] = field(default_factory=list)
    
    def freeze(self):
        """Finalisiere Driver State am Session-Ende"""
        self.final_position = self.current_position
        if self.retired or self.stopped:
            self.finishing_status = "DNF"
        elif self.laps_completed > 0:
            self.finishing_status = "Finished"


@dataclass
class LiveSessionState:
    """Kompletter Session State während Live Recording"""
    
    # Session Meta
    session_key: int
    session_name: str                    # "Race", "Qualifying"
    session_type: str                    # "Race", "Sprint", "Qualifying"
    event_name: str                      # "São Paulo Grand Prix"
    circuit_key: int
    circuit_name: str                    # "Interlagos"
    country_name: str                    # "Brazil"
    country_code: str                    # "BR"
    
    year: int
    session_date: datetime
    gmt_offset: str
    
    # Status
    session_status: str = "Started"      # "Started", "Finished", "Finalised"
    recording_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Timing
    current_lap: int = 0
    total_laps: int = 0
    session_part: Optional[int] = None   # Qualifying: 1=Q1, 2=Q2, 3=Q3
    
    # Weather
    weather: Optional[WeatherData] = None
    
    # Track Status
    track_status: str = "1"              # "1"=AllClear, "4"=Yellow, "6"=VSC, "7"=SC
    track_status_message: str = "AllClear"
    
    # Race Control
    safety_car_count: int = 0
    virtual_safety_car_count: int = 0
    red_flag_count: int = 0
    race_control_events: List[RaceControlEvent] = field(default_factory=list)
    
    # Drivers
    drivers: Dict[str, LiveDriverState] = field(default_factory=dict)
    
    # Raw State Cache (für Debugging)
    last_raw_state: Optional[dict] = None
    
    def freeze(self):
        """Freeze State am Session-Ende für Export"""
        self.session_status = "Frozen"
        for driver in self.drivers.values():
            driver.freeze()
