# Live Recorder Module Concept
**Projekt:** Looney F1 Tool - Live Recording Feature  
**Datum:** 21. November 2025  
**Status:** Schritt 2 - Konzept Design

---

## 1. Modul-Architektur

```
live_recorder/
├── __init__.py
├── client.py               # SSE Client für f1-dash
├── state.py                # Session State Data Classes
├── processor.py            # Event -> State Update Logic
├── detectors/
│   ├── __init__.py
│   ├── pitstop.py         # Pitstop Detection
│   ├── race_control.py    # SC/VSC/Red Flag Parser
│   └── lap_completion.py  # Lap Change Detection
├── exporter.py            # Live State -> RLT JSON
└── recorder.py            # Orchestrator (Main Entry)
```

---

## 2. Data Classes (`state.py`)

### 2.1 Session State (Root)
```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class LiveSessionState:
    """Kompletter Session State während Live Recording"""
    
    # Session Meta
    session_key: int
    session_name: str                    # "Race", "Qualifying"
    session_type: str                    # "Race", "Sprint", "Qualifying"
    event_name: str                      # "São Paulo Grand Prix"
    circuit_key: int
    circuit_name: str
    country_name: str
    country_code: str
    
    year: int
    session_date: datetime
    gmt_offset: str
    
    # Status
    session_status: str = "Started"      # "Started", "Finished", "Finalised"
    recording_started_at: datetime = field(default_factory=datetime.utcnow)
    
    # Timing
    current_lap: int = 0
    total_laps: int = 0
    session_part: Optional[int] = None   # Qualifying: 1=Q1, 2=Q2, 3=Q3
    
    # Weather
    weather: Optional['WeatherData'] = None
    
    # Track Status
    track_status: str = "1"              # "1"=AllClear, "4"=Yellow, "6"=VSC, "7"=SC
    track_status_message: str = "AllClear"
    
    # Race Control
    safety_car_count: int = 0
    virtual_safety_car_count: int = 0
    red_flag_count: int = 0
    race_control_events: List['RaceControlEvent'] = field(default_factory=list)
    
    # Drivers
    drivers: Dict[str, 'LiveDriverState'] = field(default_factory=dict)
    
    # Raw State Cache (für Debugging)
    last_raw_state: Optional[dict] = None
    
    def freeze(self):
        """Freeze State am Session-Ende für Export"""
        self.session_status = "Frozen"
        for driver in self.drivers.values():
            driver.freeze()

@dataclass
class WeatherData:
    air_temp: str              # Celsius
    track_temp: str
    humidity: str              # Prozent
    rainfall: bool             # True wenn Regen
    wind_speed: str            # km/h
    wind_direction: str        # Grad
```

### 2.2 Driver State
```python
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
    grid_position: int         # Startposition
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
    stints: List['StintData'] = field(default_factory=list)
    pitstops: List['PitstopData'] = field(default_factory=list)
    
    # Lap History (optional, für Analytics)
    lap_history: List['LapData'] = field(default_factory=list)
    
    def freeze(self):
        """Finalisiere Driver State am Session-Ende"""
        self.final_position = self.current_position
        if self.retired or self.stopped:
            self.finishing_status = "DNF"
        elif self.laps_completed > 0:
            self.finishing_status = "Finished"

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
class LapData:
    """Lap Timing (optional)"""
    lap_number: int
    laptime: Optional[str]
    sector_1: Optional[str]
    sector_2: Optional[str]
    sector_3: Optional[str]
    position: int
    gap_to_leader: str
```

### 2.3 Race Control Events
```python
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
```

---

## 3. Event Processing Pipeline (`processor.py`)

### 3.1 Main Processor
```python
class LiveEventProcessor:
    """Verarbeitet f1-dash Events und aktualisiert Session State"""
    
    def __init__(self, state: LiveSessionState):
        self.state = state
        self.lap_detector = LapCompletionDetector(state)
        self.pitstop_detector = PitstopDetector(state)
        self.rc_parser = RaceControlParser(state)
    
    def process_initial(self, initial_data: dict):
        """Verarbeitet Initial-Event von f1-dash"""
        # Session Info
        if session_info := initial_data.get("sessionInfo"):
            self._update_session_info(session_info)
        
        # Driver List
        if driver_list := initial_data.get("driverList"):
            self._initialize_drivers(driver_list)
        
        # Timing App Data (Grid Positions, initial Stints)
        if timing_app := initial_data.get("timingAppData"):
            self._update_timing_app_data(timing_app)
        
        # Lap Count
        if lap_count := initial_data.get("lapCount"):
            self.state.current_lap = lap_count.get("currentLap", 0)
            self.state.total_laps = lap_count.get("totalLaps", 0)
        
        # Weather
        if weather := initial_data.get("weatherData"):
            self._update_weather(weather)
        
        # Race Control (historische Messages)
        if rc_messages := initial_data.get("raceControlMessages"):
            self.rc_parser.parse_initial_messages(rc_messages.get("messages", []))
    
    def process_update(self, update_data: dict):
        """Verarbeitet Update-Events (inkrementell)"""
        
        # Lap Count Change → Neue Runde
        if lap_count := update_data.get("lapCount"):
            new_lap = lap_count.get("currentLap")
            if new_lap and new_lap != self.state.current_lap:
                self.lap_detector.on_lap_change(new_lap)
                self.state.current_lap = new_lap
        
        # Timing Data Updates
        if timing_data := update_data.get("timingData"):
            self._update_timing_data(timing_data)
        
        # Timing App Data (Stints)
        if timing_app := update_data.get("timingAppData"):
            self._update_timing_app_data(timing_app)
            self.pitstop_detector.check_stint_changes(timing_app)
        
        # Track Status
        if track_status := update_data.get("trackStatus"):
            self._update_track_status(track_status)
        
        # Session Status
        if session_status := update_data.get("sessionStatus"):
            self.state.session_status = session_status.get("status", self.state.session_status)
        
        # Race Control Messages
        if rc_messages := update_data.get("raceControlMessages"):
            self.rc_parser.parse_new_messages(rc_messages.get("messages", []))
        
        # Weather Update
        if weather := update_data.get("weatherData"):
            self._update_weather(weather)
```

### 3.2 Helper Methods
```python
    def _update_session_info(self, session_info: dict):
        meeting = session_info.get("meeting", {})
        self.state.event_name = meeting.get("name", "Unknown")
        self.state.circuit_name = meeting.get("circuit", {}).get("shortName", "Unknown")
        self.state.country_code = meeting.get("country", {}).get("code", "")
        self.state.session_name = session_info.get("name", "")
        self.state.session_type = session_info.get("type", "")
        # ...
    
    def _initialize_drivers(self, driver_list: dict):
        for number, driver_data in driver_list.items():
            driver_state = LiveDriverState(
                racing_number=number,
                tla=driver_data.get("tla", ""),
                full_name=driver_data.get("fullName", ""),
                # ...
            )
            self.state.drivers[number] = driver_state
    
    def _update_timing_data(self, timing_data: dict):
        lines = timing_data.get("lines", {})
        for number, driver_timing in lines.items():
            if driver := self.state.drivers.get(number):
                # Position Update
                if pos := driver_timing.get("position"):
                    driver.current_position = int(pos)
                
                # Laptime Update
                if last_lap := driver_timing.get("lastLapTime"):
                    driver.last_laptime = last_lap.get("value")
                
                if best_lap := driver_timing.get("bestLapTime"):
                    driver.best_laptime = best_lap.get("value")
                
                # Status Flags
                driver.in_pit = driver_timing.get("inPit", False)
                driver.pit_out = driver_timing.get("pitOut", False)
                driver.retired = driver_timing.get("retired", False)
                driver.stopped = driver_timing.get("stopped", False)
    
    def _update_timing_app_data(self, timing_app: dict):
        lines = timing_app.get("lines", {})
        for number, app_data in lines.items():
            if driver := self.state.drivers.get(number):
                # Grid Position (nur beim ersten Mal)
                if grid_pos := app_data.get("gridPos"):
                    if driver.grid_position == 0:
                        driver.grid_position = int(grid_pos)
                
                # Stints Update
                if stints := app_data.get("stints"):
                    self._update_stints(driver, stints)
    
    def _update_stints(self, driver: LiveDriverState, stints_data: list):
        """Aktualisiere Stint-Liste des Fahrers"""
        current_stint_count = len(driver.stints)
        new_stint_count = len(stints_data)
        
        if new_stint_count > current_stint_count:
            # Neuer Stint hinzugefügt
            for i in range(current_stint_count, new_stint_count):
                stint_data = stints_data[i]
                stint = StintData(
                    stint_number=i + 1,
                    compound=stint_data.get("compound", "UNKNOWN"),
                    is_new=stint_data.get("new") == "TRUE",
                    total_laps=stint_data.get("totalLaps", 0)
                )
                driver.stints.append(stint)
        else:
            # Existierende Stints aktualisieren (totalLaps)
            for i, stint_data in enumerate(stints_data):
                if i < len(driver.stints):
                    driver.stints[i].total_laps = stint_data.get("totalLaps", 0)
```

---

## 4. Detectors

### 4.1 Lap Completion Detector (`detectors/lap_completion.py`)
```python
class LapCompletionDetector:
    """Erkennt Runden-Abschluss und extrahiert Lap Data"""
    
    def __init__(self, state: LiveSessionState):
        self.state = state
    
    def on_lap_change(self, new_lap: int):
        """Wird aufgerufen wenn current_lap sich ändert"""
        print(f"[LAP] Lap {new_lap} started")
        
        # Für alle Fahrer: Lap Data speichern
        for driver in self.state.drivers.values():
            if driver.last_laptime:
                lap_data = LapData(
                    lap_number=new_lap - 1,
                    laptime=driver.last_laptime,
                    sector_1=driver.best_sectors[0],
                    sector_2=driver.best_sectors[1],
                    sector_3=driver.best_sectors[2],
                    position=driver.current_position,
                    gap_to_leader="0.0"  # TODO: Aus timingData extrahieren
                )
                driver.lap_history.append(lap_data)
                driver.laps_completed = new_lap - 1
```

### 4.2 Pitstop Detector (`detectors/pitstop.py`)
```python
class PitstopDetector:
    """Erkennt Boxenstopps via Stint-Changes"""
    
    def __init__(self, state: LiveSessionState):
        self.state = state
        self.previous_stint_counts: Dict[str, int] = {}
    
    def check_stint_changes(self, timing_app_data: dict):
        """Prüft ob Fahrer neuen Stint begonnen haben"""
        lines = timing_app_data.get("lines", {})
        
        for number, app_data in lines.items():
            stints = app_data.get("stints", [])
            current_stint_count = len(stints)
            previous_count = self.previous_stint_counts.get(number, 0)
            
            if current_stint_count > previous_count and previous_count > 0:
                # Pitstop erkannt!
                driver = self.state.drivers.get(number)
                if driver:
                    self._register_pitstop(driver, stints)
            
            self.previous_stint_counts[number] = current_stint_count
    
    def _register_pitstop(self, driver: LiveDriverState, stints: list):
        """Registriere Pitstop im Driver State"""
        stop_number = len(driver.pitstops) + 1
        
        # Compound In/Out
        compound_in = stints[-2].get("compound", "UNKNOWN") if len(stints) >= 2 else "START"
        compound_out = stints[-1].get("compound", "UNKNOWN")
        
        pitstop = PitstopData(
            stop_number=stop_number,
            lap=self.state.current_lap,
            compound_in=compound_in,
            compound_out=compound_out
        )
        driver.pitstops.append(pitstop)
        
        print(f"[PITSTOP] {driver.tla} - Stop {stop_number} on Lap {self.state.current_lap}: {compound_in} → {compound_out}")
```

### 4.3 Race Control Parser (`detectors/race_control.py`)
```python
class RaceControlParser:
    """Parsed Race Control Messages für SC/VSC/Red Flag"""
    
    def __init__(self, state: LiveSessionState):
        self.state = state
        self.processed_timestamps: set = set()  # Dedup
    
    def parse_initial_messages(self, messages: list):
        """Parse historische Messages beim Initial-Event"""
        for msg in messages:
            self._parse_message(msg)
    
    def parse_new_messages(self, messages: list):
        """Parse neue Messages aus Updates"""
        for msg in messages:
            timestamp = msg.get("utc")
            if timestamp not in self.processed_timestamps:
                self._parse_message(msg)
                self.processed_timestamps.add(timestamp)
    
    def _parse_message(self, msg: dict):
        """Parse einzelne Message"""
        category = msg.get("category", "Other")
        message_text = msg.get("message", "")
        
        event = RaceControlEvent(
            timestamp=self._parse_timestamp(msg.get("utc")),
            lap=msg.get("lap", 0),
            category=category,
            message=message_text,
            flag=msg.get("flag"),
            scope=msg.get("scope")
        )
        self.state.race_control_events.append(event)
        
        # Count SC/VSC/Red Flag
        if category == "SafetyCar":
            if "SAFETY CAR" in message_text and "VIRTUAL" not in message_text:
                self.state.safety_car_count += 1
                print(f"[RC] Safety Car deployed (Total: {self.state.safety_car_count})")
            elif "VIRTUAL SAFETY CAR" in message_text:
                self.state.virtual_safety_car_count += 1
                print(f"[RC] Virtual Safety Car deployed (Total: {self.state.virtual_safety_car_count})")
        
        if msg.get("flag") == "RED":
            self.state.red_flag_count += 1
            print(f"[RC] Red Flag (Total: {self.state.red_flag_count})")
    
    def _parse_timestamp(self, utc_str: str) -> datetime:
        from dateutil.parser import parse
        return parse(utc_str)
```

---

## 5. SSE Client (`client.py`)

```python
import sseclient
import requests
from typing import Callable

class F1DashClient:
    """SSE Client für f1-dash Live Service"""
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url
        self.sse_url = f"{base_url}/api/sse"
    
    def connect(
        self,
        on_initial: Callable[[dict], None],
        on_update: Callable[[dict], None],
        on_error: Callable[[Exception], None]
    ):
        """Verbinde zu SSE Stream und verarbeite Events"""
        try:
            response = requests.get(self.sse_url, stream=True, timeout=10)
            response.raise_for_status()
            
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.event == "initial":
                    data = json.loads(event.data)
                    on_initial(data)
                elif event.event == "update":
                    data = json.loads(event.data)
                    on_update(data)
                    
        except Exception as e:
            on_error(e)
    
    def get_drivers(self) -> list:
        """Abrufen der Fahrerliste via REST"""
        response = requests.get(f"{self.base_url}/api/drivers")
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> bool:
        """Health Check"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.json().get("success", False)
        except:
            return False
```

---

## 6. Exporter (`exporter.py`)

```python
class LiveToRLTExporter:
    """Exportiert Live Session State zu RLT JSON"""
    
    def __init__(self, state: LiveSessionState):
        self.state = state
    
    def export(self) -> dict:
        """Generiere RLT-kompatibles JSON"""
        
        # Meta Block
        meta = self._build_meta()
        
        # Driver Blocks
        drivers = []
        for driver_state in self.state.drivers.values():
            driver_block = self._build_driver_block(driver_state)
            drivers.append(driver_block)
        
        # Sort by final position
        drivers.sort(key=lambda d: d["EndPosition"])
        
        return {
            "Meta": meta,
            "Drivers": drivers
        }
    
    def _build_meta(self) -> dict:
        """Meta Block aus Live State"""
        return {
            "Event": self.state.event_name,
            "Track": self.state.circuit_name,
            "Year": self.state.year,
            "Session": self.state.session_type,
            "Date": self.state.session_date.isoformat(),
            "Weather": {
                "AirTemp": self.state.weather.air_temp if self.state.weather else "0",
                "TrackTemp": self.state.weather.track_temp if self.state.weather else "0",
                "Rainfall": self.state.weather.rainfall if self.state.weather else False
            },
            "RaceControl": {
                "SafetyCarCount": self.state.safety_car_count,
                "VirtualSafetyCarCount": self.state.virtual_safety_car_count,
                "RedFlagCount": self.state.red_flag_count
            }
        }
    
    def _build_driver_block(self, driver: LiveDriverState) -> dict:
        """Driver Block aus Live Driver State"""
        
        # Mappings anwenden (via bestehende Module)
        from mapping.drivers_aliases import get_driver_id
        from mapping.drivers_nations import get_nation
        from mapping.teams_aliases import get_team_id
        
        # Pitstops Array
        pitstops = [
            {
                "Lap": ps.lap,
                "Compound": ps.compound_out,
                "StopCount": ps.stop_number
            }
            for ps in driver.pitstops
        ]
        
        return {
            "Name": driver.full_name,
            "Number": driver.racing_number,
            "Team": get_team_id(driver.team_name),
            "Nation": get_nation(driver.country_code),
            "StartPosition": driver.grid_position,
            "EndPosition": driver.final_position or driver.current_position,
            "Laps": driver.laps_completed,
            "Status": driver.finishing_status,
            "BestLaptime": driver.best_laptime,
            "Pitstops": pitstops
        }
```

---

## 7. Main Recorder Orchestrator (`recorder.py`)

```python
class LiveRecorder:
    """Orchestrator für Live Recording"""
    
    def __init__(self, f1dash_url: str, output_dir: str):
        self.f1dash_url = f1dash_url
        self.output_dir = output_dir
        self.client = F1DashClient(f1dash_url)
        self.state: Optional[LiveSessionState] = None
        self.processor: Optional[LiveEventProcessor] = None
    
    def start_recording(self):
        """Start Live Recording"""
        print(f"[RECORDER] Connecting to f1-dash at {self.f1dash_url}...")
        
        # Health Check
        if not self.client.health_check():
            raise ConnectionError("f1-dash is not reachable!")
        
        print("[RECORDER] Starting recording...")
        
        self.client.connect(
            on_initial=self._on_initial,
            on_update=self._on_update,
            on_error=self._on_error
        )
    
    def _on_initial(self, data: dict):
        """Initial Event Handler"""
        print("[RECORDER] Received initial state")
        
        # Initialize Session State
        self.state = self._create_session_state(data)
        self.processor = LiveEventProcessor(self.state)
        
        # Process Initial Data
        self.processor.process_initial(data)
        
        print(f"[RECORDER] Recording session: {self.state.event_name} - {self.state.session_name}")
        print(f"[RECORDER] {len(self.state.drivers)} drivers initialized")
    
    def _on_update(self, data: dict):
        """Update Event Handler"""
        if not self.processor:
            return
        
        self.processor.process_update(data)
        
        # Check Session Ende
        if self.state.session_status in ["Finished", "Finalised"]:
            self._finalize_recording()
    
    def _on_error(self, error: Exception):
        """Error Handler"""
        print(f"[ERROR] {error}")
        # TODO: Reconnect Logic
    
    def _finalize_recording(self):
        """Session beendet → Export"""
        print("[RECORDER] Session finished. Finalizing...")
        
        self.state.freeze()
        
        # Export to RLT JSON
        exporter = LiveToRLTExporter(self.state)
        rlt_json = exporter.export()
        
        # Save to file
        filename = f"{self.state.event_name}_{self.state.session_type}_{self.state.year}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rlt_json, f, indent=2, ensure_ascii=False)
        
        print(f"[RECORDER] Export saved to: {filepath}")
    
    def _create_session_state(self, initial_data: dict) -> LiveSessionState:
        """Erstelle initialen Session State"""
        session_info = initial_data.get("sessionInfo", {})
        meeting = session_info.get("meeting", {})
        
        return LiveSessionState(
            session_key=session_info.get("key", 0),
            session_name=session_info.get("name", "Unknown"),
            session_type=session_info.get("type", "Unknown"),
            event_name=meeting.get("name", "Unknown"),
            circuit_key=meeting.get("circuit", {}).get("key", 0),
            circuit_name=meeting.get("circuit", {}).get("shortName", "Unknown"),
            country_name=meeting.get("country", {}).get("name", ""),
            country_code=meeting.get("country", {}).get("code", ""),
            year=datetime.fromisoformat(session_info.get("startDate", "")).year,
            session_date=datetime.fromisoformat(session_info.get("startDate", "")),
            gmt_offset=session_info.get("gmtOffset", "00:00:00")
        )
```

---

## 8. Integration in `main.py`

```python
# main.py

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["jolpica", "fastf1", "f1dash_live"])
    parser.add_argument("--mode", choices=["export", "record"])
    parser.add_argument("--f1dash-url", default="http://localhost:4000")
    parser.add_argument("--output-dir", default="./output")
    # ...
    
    args = parser.parse_args()
    
    if args.backend == "f1dash_live" and args.mode == "record":
        from live_recorder.recorder import LiveRecorder
        
        recorder = LiveRecorder(
            f1dash_url=args.f1dash_url,
            output_dir=args.output_dir
        )
        recorder.start_recording()
```

---

## 9. Logging

```python
import logging

# In recorder.py
logger = logging.getLogger("live_recorder")

# Setup in main.py
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(f"logs/live_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
```

---

**Ende Schritt 2 Konzept Design**

**Nächster Schritt:** Implementierung beginnen mit `state.py` und `client.py`.
