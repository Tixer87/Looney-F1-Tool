import logging
from typing import Dict,TYPE_CHECKING
if TYPE_CHECKING:
    from ..state import LiveSessionState,LiveDriverState
logger=logging.getLogger(__name__)
class PitstopDetector:
    def __init__(self,state:'LiveSessionState'):
        self.state=state
        self.previous_stint_counts:Dict[str,int]={}
    def initialize_stint_counts(self,timing_app_data:dict):
        lines=timing_app_data.get("Lines",timing_app_data.get("lines",{}))
        for number,app_data in lines.items():
            stints=app_data.get("Stints",app_data.get("stints",[]))
            self.previous_stint_counts[number]=len(stints)
        logger.info(f"Initialized stint counts for {len(self.previous_stint_counts)} drivers")
    def check_stint_changes(self,timing_app_data:dict):
        lines=timing_app_data.get("Lines",timing_app_data.get("lines",{}))
        for number,app_data in lines.items():
            stints=app_data.get("Stints",app_data.get("stints",[]))
            current=len(stints)
            previous=self.previous_stint_counts.get(number,0)
            if current>previous and previous>0:
                driver=self.state.drivers.get(number)
                if driver:self._register_pitstop(driver,stints)
            self.previous_stint_counts[number]=current
    def _register_pitstop(self,driver:'LiveDriverState',stints:list):
        from ..state import PitstopData
        stop_number=len(driver.pitstops)+1
        compound_in=stints[-2].get("Compound",stints[-2].get("compound","UNKNOWN")) if len(stints)>=2 else "START"
        compound_out=stints[-1].get("Compound",stints[-1].get("compound","UNKNOWN"))
        driver.pitstops.append(PitstopData(
            stop_number=stop_number,
            lap=self.state.current_lap,
            compound_in=compound_in,
            compound_out=compound_out
        ))
        logger.info(f"PITSTOP: {driver.tla} - Stop {stop_number} on Lap {self.state.current_lap}: {compound_in} → {compound_out}")