"""
Event Processor
Verarbeitet f1-dash Events und aktualisiert Session State
"""

import logging
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from dateutil.parser import parse as parse_datetime

if TYPE_CHECKING:
    from .state import LiveSessionState, LiveDriverState, StintData, WeatherData

from .detectors import LapCompletionDetector, PitstopDetector, RaceControlParser

logger = logging.getLogger(__name__)


class LiveEventProcessor:
    """Verarbeitet f1-dash Events und aktualisiert Session State"""
    
    def __init__(self, state: 'LiveSessionState'):
        self.state = state
        self.lap_detector = LapCompletionDetector(state)
        self.pitstop_detector = PitstopDetector(state)
        self.rc_parser = RaceControlParser(state)
    
    @staticmethod
    def create_state_from_initial(initial_data: dict) -> 'LiveSessionState':
        """
        Factory: Erstelle LiveSessionState aus f1-dash Initial Event
        
        Args:
            initial_data: Initial Event von f1-dash
            
        Returns:
            LiveSessionState mit initialisierten required fields
        """
        from .state import LiveSessionState
        
        session_info = initial_data.get("sessionInfo", {})
        meeting = session_info.get("meeting", {})
        
        # Debug
        logger.debug(f"meeting keys: {meeting.keys()}")
        logger.debug(f"location: {meeting.get('location')}")
        
        # Parse start date
        start_date_str = session_info.get("startDate", "")
        try:
            session_date = parse_datetime(start_date_str)
            year = session_date.year
        except:
            session_date = datetime.now(timezone.utc)
            year = datetime.now(timezone.utc).year
        
        # Circuit Name: location oder circuit.shortName
        circuit_name = meeting.get("location") or meeting.get("circuit", {}).get("shortName", "Unknown")
        
        return LiveSessionState(
            session_key=session_info.get("key", 0),
            session_name=session_info.get("name", "Unknown"),
            session_type=session_info.get("type", "Unknown"),
            event_name=meeting.get("name", "Unknown Event"),
            circuit_key=meeting.get("circuit", {}).get("key", 0),
            circuit_name=circuit_name,
            country_name=meeting.get("country", {}).get("name", "Unknown"),
            country_code=meeting.get("country", {}).get("code", "UNK"),
            year=year,
            session_date=session_date,
            gmt_offset=session_info.get("gmtOffset", "00:00:00")
        )
    
    def process_initial(self, initial_data: dict):
        """
        Verarbeitet Initial-Event von f1-dash
        
        Args:
            initial_data: Complete initial state from f1-dash
        """
        logger.info("Processing initial event")
        
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
            logger.info(f"Lap {self.state.current_lap}/{self.state.total_laps}")
        
        # Weather
        if weather := initial_data.get("weatherData"):
            self._update_weather(weather)
        
        # Track Status
        if track_status := initial_data.get("trackStatus"):
            self._update_track_status(track_status)
        
        # Session Status
        if session_status := initial_data.get("sessionStatus"):
            self.state.session_status = session_status.get("status", "Started")
        
        # Timing Data (Positions, Laptimes)
        if timing_data := initial_data.get("timingData"):
            self._update_timing_data(timing_data)
        
        # Race Control (historische Messages)
        if rc_messages := initial_data.get("RaceControlMessages", initial_data.get("raceControlMessages")):
            # RaceControlParser erwartet das gesamte dict (mit Messages/messages key)
            self.rc_parser.parse_initial_messages(rc_messages)
        
        # Timing App Data (Stints) - Initialisiere Pitstop Detector
        if timing_app := initial_data.get("TimingAppData", initial_data.get("timingAppData")):
            self.pitstop_detector.initialize_stint_counts(timing_app)
        
        logger.info(f"Initial state processed: {len(self.state.drivers)} drivers, {self.state.event_name}")
    
    def process_update(self, update_data: dict):
        """
        Verarbeitet Update-Events (inkrementell)
        
        Args:
            update_data: Partial update from f1-dash
        """
        
        # Timing Data Updates ZUERST (damit last_laptime verfügbar ist für Lap Detection)
        if timing_data := update_data.get("timingData"):
            self._update_timing_data(timing_data)
        
        # Lap Count Change → Neue Runde (NACH timing_data!)
        if lap_count := update_data.get("lapCount"):
            new_lap = lap_count.get("currentLap")
            if new_lap and new_lap != self.state.current_lap:
                self.lap_detector.on_lap_change(new_lap)
                self.state.current_lap = new_lap
        
        # Timing App Data (Stints)
        if timing_app := update_data.get("timingAppData"):
            self._update_timing_app_data(timing_app)
            self.pitstop_detector.check_stint_changes(timing_app)
        
        # Track Status
        if track_status := update_data.get("trackStatus"):
            self._update_track_status(track_status)
        
        # Session Status
        if session_status := update_data.get("sessionStatus"):
            new_status = session_status.get("status", self.state.session_status)
            if new_status != self.state.session_status:
                logger.info(f"Session status changed: {self.state.session_status} → {new_status}")
                self.state.session_status = new_status
        
        # Race Control Messages
        if rc_messages := update_data.get("RaceControlMessages", update_data.get("raceControlMessages")):
            # parse_new_messages erwartet direkt Messages Array
            messages_list = rc_messages.get("Messages", rc_messages.get("messages", []))
            self.rc_parser.parse_new_messages(messages_list)
        
        # Weather Update
        if weather := update_data.get("weatherData"):
            self._update_weather(weather)
    
    def _update_session_info(self, session_info: dict):
        """Update Session Info"""
        meeting = session_info.get("meeting", {})
        self.state.event_name = meeting.get("name", "Unknown")
        self.state.circuit_key = meeting.get("circuit", {}).get("key", 0)
        
        # Circuit Name: location oder circuit.shortName
        self.state.circuit_name = (
            meeting.get("location") or 
            meeting.get("circuit", {}).get("shortName", "Unknown")
        )
        
        self.state.country_name = meeting.get("country", {}).get("name", "")
        self.state.country_code = meeting.get("country", {}).get("code", "")
        self.state.session_name = session_info.get("name", "")
        self.state.session_type = session_info.get("type", "")
        self.state.session_key = session_info.get("key", 0)
        self.state.gmt_offset = session_info.get("gmtOffset", "00:00:00")
        
        # Parse dates
        if start_date := session_info.get("startDate"):
            try:
                self.state.session_date = parse_datetime(start_date)
                self.state.year = self.state.session_date.year
            except:
                pass
    
    def _initialize_drivers(self, driver_list: dict):
        """Initialize Driver States"""
        from .state import LiveDriverState
        
        for number, driver_data in driver_list.items():
            driver_state = LiveDriverState(
                racing_number=number,
                tla=driver_data.get("tla", ""),
                full_name=driver_data.get("fullName", ""),
                broadcast_name=driver_data.get("broadcastName", ""),
                first_name=driver_data.get("firstName", ""),
                last_name=driver_data.get("lastName", ""),
                team_name=driver_data.get("teamName", ""),
                team_colour=driver_data.get("teamColour", ""),
                country_code=driver_data.get("countryCode", "")
            )
            self.state.drivers[number] = driver_state
        
        logger.info(f"Initialized {len(self.state.drivers)} drivers")
    
    def _update_timing_data(self, timing_data: dict):
        """Update Timing Data (Positions, Laptimes)"""
        # Session Part (Qualifying)
        session_part = timing_data.get("SessionPart", timing_data.get("sessionPart"))
        if session_part:
            self.state.session_part = session_part
        
        lines = timing_data.get("Lines", timing_data.get("lines", {}))
        for number, driver_timing in lines.items():
            if driver := self.state.drivers.get(number):
                # Position Update
                pos = driver_timing.get("Position", driver_timing.get("position"))
                if pos:
                    try:
                        driver.current_position = int(pos)
                    except:
                        pass
                
                # Laptime Update
                last_lap = driver_timing.get("LastLapTime", driver_timing.get("lastLapTime"))
                if last_lap:
                    value = last_lap.get("Value", last_lap.get("value"))
                    if value:
                        driver.last_laptime = value
                
                best_lap = driver_timing.get("BestLapTime", driver_timing.get("bestLapTime"))
                if best_lap:
                    value = best_lap.get("Value", best_lap.get("value"))
                    if value:
                        driver.best_laptime = value
                
                # Sectors
                sectors = driver_timing.get("Sectors", driver_timing.get("sectors"))
                if sectors:
                    for i, sector in enumerate(sectors[:3]):
                        value = sector.get("Value", sector.get("value"))
                        if value:
                            if i < len(driver.best_sectors):
                                driver.best_sectors[i] = value
                
                # Status Flags
                driver.in_pit = driver_timing.get("InPit", driver_timing.get("inPit", False))
                driver.pit_out = driver_timing.get("PitOut", driver_timing.get("pitOut", False))
                driver.retired = driver_timing.get("Retired", driver_timing.get("retired", False))
                driver.stopped = driver_timing.get("Stopped", driver_timing.get("stopped", False))
                driver.knocked_out = driver_timing.get("KnockedOut", driver_timing.get("knockedOut", False))
    
    def _update_timing_app_data(self, timing_app: dict):
        """Update Timing App Data (Grid, Stints)"""
        lines = timing_app.get("Lines", timing_app.get("lines", {}))
        for number, app_data in lines.items():
            if driver := self.state.drivers.get(number):
                # Grid Position (nur beim ersten Mal)
                grid_pos = app_data.get("GridPos", app_data.get("gridPos"))
                if grid_pos:
                    try:
                        if driver.grid_position == 0:
                            driver.grid_position = int(grid_pos)
                    except:
                        pass
                
                # Stints Update
                stints = app_data.get("Stints", app_data.get("stints"))
                if stints:
                    self._update_stints(driver, stints)
    
    def _update_stints(self, driver: 'LiveDriverState', stints_data: list):
        """Aktualisiere Stint-Liste des Fahrers"""
        from .state import StintData
        
        current_stint_count = len(driver.stints)
        new_stint_count = len(stints_data)
        
        if new_stint_count > current_stint_count:
            # Neuer Stint hinzugefügt
            for i in range(current_stint_count, new_stint_count):
                stint_data = stints_data[i]
                compound = stint_data.get("Compound", stint_data.get("compound", "UNKNOWN"))
                is_new = stint_data.get("New", stint_data.get("new", "false")).upper() == "TRUE"
                total_laps = stint_data.get("TotalLaps", stint_data.get("totalLaps", 0))
                
                stint = StintData(
                    stint_number=i + 1,
                    compound=compound,
                    is_new=is_new,
                    total_laps=total_laps
                )
                driver.stints.append(stint)
        else:
            # Existierende Stints aktualisieren (totalLaps)
            for i, stint_data in enumerate(stints_data):
                if i < len(driver.stints):
                    total_laps = stint_data.get("TotalLaps", stint_data.get("totalLaps", 0))
                    driver.stints[i].total_laps = total_laps
    
    def _update_weather(self, weather_data: dict):
        """Update Weather Data"""
        from .state import WeatherData
        
        air_temp = weather_data.get("AirTemp", weather_data.get("airTemp", "0"))
        track_temp = weather_data.get("TrackTemp", weather_data.get("trackTemp", "0"))
        humidity = weather_data.get("Humidity", weather_data.get("humidity", "0"))
        rainfall = weather_data.get("Rainfall", weather_data.get("rainfall", "0")) == "1"
        wind_speed = weather_data.get("WindSpeed", weather_data.get("windSpeed", "0"))
        
        self.state.weather = WeatherData(
            air_temp=air_temp,
            track_temp=track_temp,
            humidity=humidity,
            rainfall=rainfall,
            wind_speed=wind_speed,
            wind_direction=weather_data.get("WindDirection", weather_data.get("windDirection", "0"))
        )
    
    def _update_track_status(self, track_status: dict):
        """Update Track Status"""
        self.state.track_status = track_status.get("Status", track_status.get("status", "1"))
        self.state.track_status_message = track_status.get("Message", track_status.get("message", "AllClear"))
