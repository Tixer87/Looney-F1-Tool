import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..state import LiveSessionState
logger=logging.getLogger(__name__)
class LapCompletionDetector:
    def __init__(self,state:'LiveSessionState'):
        self.state=state
    def on_lap_change(self,new_lap:int):
        logger.info(f"Lap {new_lap} started")
        from ..state import LapData
        for driver in self.state.drivers.values():
            if driver.retired or driver.stopped:continue
            if driver.last_laptime:
                driver.lap_history.append(LapData(
                    lap_number=new_lap,
                    laptime=driver.last_laptime,
                    sector_1=driver.best_sectors[0],
                    sector_2=driver.best_sectors[1],
                    sector_3=driver.best_sectors[2],
                    position=driver.current_position,
                    gap_to_leader="0.0"
                ))
                driver.laps_completed+=1