from dataclasses import dataclass,field
from datetime import datetime,timezone
from typing import Dict,List,Optional
@dataclass
class WeatherData:
    air_temp:str
    track_temp:str
    humidity:str
    rainfall:bool
    wind_speed:str
    wind_direction:str
@dataclass
class RaceControlEvent:
    timestamp:datetime
    lap:int
    category:str
    message:str
    flag:Optional[str]=None
    scope:Optional[str]=None
    driver_number:Optional[str]=None
@dataclass
class LapData:
    lap_number:int
    laptime:Optional[str]
    sector_1:Optional[str]
    sector_2:Optional[str]
    sector_3:Optional[str]
    position:int
    gap_to_leader:str
@dataclass
class StintData:
    stint_number:int
    compound:str
    is_new:bool
    start_lap:Optional[int]=None
    end_lap:Optional[int]=None
    total_laps:int=0
@dataclass
class PitstopData:
    stop_number:int
    lap:int
    compound_in:str
    compound_out:str
    duration_estimate:Optional[float]=None
@dataclass
class LiveDriverState:
    racing_number:str
    tla:str
    full_name:str
    broadcast_name:str
    first_name:str
    last_name:str
    team_name:str
    team_colour:str
    country_code:str
    grid_position:int=0
    current_position:int=0
    final_position:Optional[int]=None
    laps_completed:int=0
    best_laptime:Optional[str]=None
    last_laptime:Optional[str]=None
    best_sectors:List[Optional[str]]=field(default_factory=lambda:[None,None,None])
    in_pit:bool=False
    pit_out:bool=False
    retired:bool=False
    stopped:bool=False
    knocked_out:bool=False
    finishing_status:str="Running"
    stints:List[StintData]=field(default_factory=list)
    pitstops:List[PitstopData]=field(default_factory=list)
    lap_history:List[LapData]=field(default_factory=list)
    def freeze(self):
        self.final_position=self.current_position
        if self.retired or self.stopped:self.finishing_status="DNF"
        elif self.laps_completed>0:self.finishing_status="Finished"
@dataclass
class LiveSessionState:
    session_key:int
    session_name:str
    session_type:str
    event_name:str
    circuit_key:int
    circuit_name:str
    country_name:str
    country_code:str
    year:int
    session_date:datetime
    gmt_offset:str
    session_status:str="Started"
    recording_started_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    current_lap:int=0
    total_laps:int=0
    session_part:Optional[int]=None
    weather:Optional[WeatherData]=None
    track_status:str="1"
    track_status_message:str="AllClear"
    safety_car_count:int=0
    virtual_safety_car_count:int=0
    red_flag_count:int=0
    race_control_events:List[RaceControlEvent]=field(default_factory=list)
    drivers:Dict[str,LiveDriverState]=field(default_factory=dict)
    last_raw_state:Optional[dict]=None
    def freeze(self):
        self.session_status="Frozen"
        for driver in self.drivers.values():driver.freeze()