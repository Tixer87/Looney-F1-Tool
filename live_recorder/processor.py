import logging
from datetime import datetime,timezone
from typing import TYPE_CHECKING
from dateutil.parser import parse as parse_datetime
from .detectors import LapCompletionDetector,PitstopDetector,RaceControlParser
if TYPE_CHECKING:
    from .state import LiveSessionState,LiveDriverState
logger=logging.getLogger(__name__)
class LiveEventProcessor:
    def __init__(self,state:'LiveSessionState'):
        self.state=state
        self.lap_detector=LapCompletionDetector(state)
        self.pitstop_detector=PitstopDetector(state)
        self.rc_parser=RaceControlParser(state)
    @staticmethod
    def create_state_from_initial(initial_data:dict)->'LiveSessionState':
        from .state import LiveSessionState
        session_info=initial_data.get("sessionInfo",{})
        meeting=session_info.get("meeting",{})
        start=session_info.get("startDate","")
        try:
            session_date=parse_datetime(start)
            year=session_date.year
        except Exception:
            session_date=datetime.now(timezone.utc)
            year=session_date.year
        return LiveSessionState(
            session_key=session_info.get("key",0),
            session_name=session_info.get("name","Unknown"),
            session_type=session_info.get("type","Unknown"),
            event_name=meeting.get("name","Unknown Event"),
            circuit_key=meeting.get("circuit",{}).get("key",0),
            circuit_name=meeting.get("location") or meeting.get("circuit",{}).get("shortName","Unknown"),
            country_name=meeting.get("country",{}).get("name","Unknown"),
            country_code=meeting.get("country",{}).get("code","UNK"),
            year=year,
            session_date=session_date,
            gmt_offset=session_info.get("gmtOffset","00:00:00")
        )
    def process_initial(self,initial_data:dict):
        logger.info("Processing initial event")
        if session_info:=initial_data.get("sessionInfo"):self._update_session_info(session_info)
        if driver_list:=initial_data.get("driverList"):self._initialize_drivers(driver_list)
        if timing_app:=initial_data.get("timingAppData"):self._update_timing_app_data(timing_app)
        if lap_count:=initial_data.get("lapCount"):
            self.state.current_lap=lap_count.get("currentLap",0)
            self.state.total_laps=lap_count.get("totalLaps",0)
            logger.info(f"Lap {self.state.current_lap}/{self.state.total_laps}")
        if weather:=initial_data.get("weatherData"):self._update_weather(weather)
        if track_status:=initial_data.get("trackStatus"):self._update_track_status(track_status)
        if session_status:=initial_data.get("sessionStatus"):self.state.session_status=session_status.get("status","Started")
        if timing_data:=initial_data.get("timingData"):self._update_timing_data(timing_data)
        if messages:=initial_data.get("RaceControlMessages",initial_data.get("raceControlMessages")):self.rc_parser.parse_initial_messages(messages)
        if timing_app:=initial_data.get("TimingAppData",initial_data.get("timingAppData")):self.pitstop_detector.initialize_stint_counts(timing_app)
        logger.info(f"Initial state processed: {len(self.state.drivers)} drivers, {self.state.event_name}")
    def process_update(self,update_data:dict):
        if timing_data:=update_data.get("timingData"):self._update_timing_data(timing_data)
        if lap_count:=update_data.get("lapCount"):
            new_lap=lap_count.get("currentLap")
            if new_lap and new_lap!=self.state.current_lap:
                self.lap_detector.on_lap_change(new_lap)
                self.state.current_lap=new_lap
        if timing_app:=update_data.get("timingAppData"):
            self._update_timing_app_data(timing_app)
            self.pitstop_detector.check_stint_changes(timing_app)
        if track_status:=update_data.get("trackStatus"):self._update_track_status(track_status)
        if session_status:=update_data.get("sessionStatus"):
            new_status=session_status.get("status",self.state.session_status)
            if new_status!=self.state.session_status:
                logger.info(f"Session status changed: {self.state.session_status} → {new_status}")
                self.state.session_status=new_status
        if messages:=update_data.get("RaceControlMessages",update_data.get("raceControlMessages")):
            self.rc_parser.parse_new_messages(messages.get("Messages",messages.get("messages",[])))
        if weather:=update_data.get("weatherData"):self._update_weather(weather)
    def _update_session_info(self,session_info:dict):
        meeting=session_info.get("meeting",{})
        self.state.event_name=meeting.get("name","Unknown")
        self.state.circuit_key=meeting.get("circuit",{}).get("key",0)
        self.state.circuit_name=meeting.get("location") or meeting.get("circuit",{}).get("shortName","Unknown")
        self.state.country_name=meeting.get("country",{}).get("name","")
        self.state.country_code=meeting.get("country",{}).get("code","")
        self.state.session_name=session_info.get("name","")
        self.state.session_type=session_info.get("type","")
        self.state.session_key=session_info.get("key",0)
        self.state.gmt_offset=session_info.get("gmtOffset","00:00:00")
        if start:=session_info.get("startDate"):
            try:
                self.state.session_date=parse_datetime(start)
                self.state.year=self.state.session_date.year
            except Exception:
                pass
    def _initialize_drivers(self,driver_list:dict):
        from .state import LiveDriverState
        for number,data in driver_list.items():
            self.state.drivers[number]=LiveDriverState(
                racing_number=number,
                tla=data.get("tla",""),
                full_name=data.get("fullName",""),
                broadcast_name=data.get("broadcastName",""),
                first_name=data.get("firstName",""),
                last_name=data.get("lastName",""),
                team_name=data.get("teamName",""),
                team_colour=data.get("teamColour",""),
                country_code=data.get("countryCode","")
            )
        logger.info(f"Initialized {len(self.state.drivers)} drivers")
    def _update_timing_data(self,timing_data:dict):
        session_part=timing_data.get("SessionPart",timing_data.get("sessionPart"))
        if session_part:self.state.session_part=session_part
        lines=timing_data.get("Lines",timing_data.get("lines",{}))
        for number,data in lines.items():
            driver=self.state.drivers.get(number)
            if not driver:continue
            pos=data.get("Position",data.get("position"))
            if pos:
                try:driver.current_position=int(pos)
                except (TypeError,ValueError):pass
            last=data.get("LastLapTime",data.get("lastLapTime"))
            if last:
                value=last.get("Value",last.get("value"))
                if value:driver.last_laptime=value
            best=data.get("BestLapTime",data.get("bestLapTime"))
            if best:
                value=best.get("Value",best.get("value"))
                if value:driver.best_laptime=value
            sectors=data.get("Sectors",data.get("sectors"))
            if sectors:
                for i,sector in enumerate(sectors[:3]):
                    value=sector.get("Value",sector.get("value"))
                    if value and i<len(driver.best_sectors):driver.best_sectors[i]=value
            driver.in_pit=data.get("InPit",data.get("inPit",False))
            driver.pit_out=data.get("PitOut",data.get("pitOut",False))
            driver.retired=data.get("Retired",data.get("retired",False))
            driver.stopped=data.get("Stopped",data.get("stopped",False))
            driver.knocked_out=data.get("KnockedOut",data.get("knockedOut",False))
    def _update_timing_app_data(self,timing_app:dict):
        lines=timing_app.get("Lines",timing_app.get("lines",{}))
        for number,data in lines.items():
            driver=self.state.drivers.get(number)
            if not driver:continue
            grid=data.get("GridPos",data.get("gridPos"))
            if grid and driver.grid_position==0:
                try:driver.grid_position=int(grid)
                except (TypeError,ValueError):pass
            stints=data.get("Stints",data.get("stints"))
            if stints:self._update_stints(driver,stints)
    def _update_stints(self,driver:'LiveDriverState',stints_data:list):
        from .state import StintData
        current=len(driver.stints)
        if len(stints_data)>current:
            for i in range(current,len(stints_data)):
                data=stints_data[i]
                value=data.get("New",data.get("new","false"))
                driver.stints.append(StintData(
                    stint_number=i+1,
                    compound=data.get("Compound",data.get("compound","UNKNOWN")),
                    is_new=str(value).upper()=="TRUE",
                    total_laps=data.get("TotalLaps",data.get("totalLaps",0))
                ))
        else:
            for i,data in enumerate(stints_data):
                if i<len(driver.stints):driver.stints[i].total_laps=data.get("TotalLaps",data.get("totalLaps",0))
    def _update_weather(self,weather_data:dict):
        from .state import WeatherData
        self.state.weather=WeatherData(
            air_temp=weather_data.get("AirTemp",weather_data.get("airTemp","0")),
            track_temp=weather_data.get("TrackTemp",weather_data.get("trackTemp","0")),
            humidity=weather_data.get("Humidity",weather_data.get("humidity","0")),
            rainfall=weather_data.get("Rainfall",weather_data.get("rainfall","0"))=="1",
            wind_speed=weather_data.get("WindSpeed",weather_data.get("windSpeed","0")),
            wind_direction=weather_data.get("WindDirection",weather_data.get("windDirection","0"))
        )
    def _update_track_status(self,track_status:dict):
        self.state.track_status=track_status.get("Status",track_status.get("status","1"))
        self.state.track_status_message=track_status.get("Message",track_status.get("message","AllClear"))