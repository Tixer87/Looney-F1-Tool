import json
import logging
import os
from datetime import datetime,timezone
from typing import Optional
from .client import F1DashClient
from .exporter import LiveToRLTExporter
from .processor import LiveEventProcessor
from .state import LiveSessionState
logger=logging.getLogger(__name__)
class LiveRecorder:
    def __init__(self,f1dash_url:str,output_dir:str):
        self.f1dash_url=f1dash_url
        self.output_dir=output_dir
        self.client=F1DashClient(f1dash_url)
        self.state:Optional[LiveSessionState]=None
        self.processor:Optional[LiveEventProcessor]=None
        self.finalized=False
    def start_recording(self):
        logger.info(f"Connecting to f1-dash at {self.f1dash_url}...")
        if not self.client.health_check():raise ConnectionError(f"f1-dash is not reachable at {self.f1dash_url}!")
        logger.info("f1-dash is healthy. Starting recording...")
        os.makedirs(self.output_dir,exist_ok=True)
        self.client.connect(on_initial=self._on_initial,on_update=self._on_update,on_error=self._on_error)
    def _on_initial(self,data:dict):
        logger.info("Received initial state")
        self.state=self._create_session_state(data)
        self.processor=LiveEventProcessor(self.state)
        self.processor.process_initial(data)
        logger.info(f"Recording session: {self.state.event_name} - {self.state.session_name}")
        logger.info(f"{len(self.state.drivers)} drivers initialized")
        logger.info(f"Lap {self.state.current_lap}/{self.state.total_laps}")
    def _on_update(self,data:dict):
        if not self.processor or not self.state:return
        self.processor.process_update(data)
        if self.state.session_status in ("Finished","Finalised") and not self.finalized:self._finalize_recording()
    def _on_error(self,error:Exception):
        logger.error(f"Stream error: {error}")
        if self.state and not self.finalized:
            logger.warning("Attempting to finalize session after error...")
            self._finalize_recording()
    def _finalize_recording(self):
        if self.finalized:return
        self.finalized=True
        logger.info("Session finished. Finalizing...")
        if not self.state:
            logger.error("No state to finalize!")
            return
        self.state.freeze()
        data=LiveToRLTExporter(self.state).export()
        filepath=os.path.join(self.output_dir,self._generate_filename())
        with open(filepath,"w",encoding="utf-8") as file:json.dump(data,file,indent=2,ensure_ascii=False)
        logger.info(f"Export saved to: {filepath}")
        self._print_summary()
    def _create_session_state(self,initial_data:dict)->LiveSessionState:
        from dateutil.parser import parse as parse_datetime
        session_info=initial_data.get("sessionInfo",{})
        meeting=session_info.get("meeting",{})
        try:
            session_date=parse_datetime(session_info.get("startDate",""))
            year=session_date.year
        except Exception:
            session_date=datetime.now(timezone.utc)
            year=session_date.year
        return LiveSessionState(
            session_key=session_info.get("key",0),
            session_name=session_info.get("name","Unknown"),
            session_type=session_info.get("type","Unknown"),
            event_name=meeting.get("name","Unknown"),
            circuit_key=meeting.get("circuit",{}).get("key",0),
            circuit_name=meeting.get("circuit",{}).get("shortName","Unknown"),
            country_name=meeting.get("country",{}).get("name",""),
            country_code=meeting.get("country",{}).get("code",""),
            year=year,
            session_date=session_date,
            gmt_offset=session_info.get("gmtOffset","00:00:00")
        )
    def _generate_filename(self)->str:
        if not self.state:return "unknown_session.json"
        event=self.state.event_name.replace(" ","_").replace("/","-")
        session=self.state.session_type.replace(" ","_")
        return f"{event}_{session}_{self.state.year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    def _print_summary(self):
        if not self.state:return
        logger.info("="*60)
        logger.info("RECORDING SUMMARY")
        logger.info("="*60)
        logger.info(f"Event: {self.state.event_name}")
        logger.info(f"Session: {self.state.session_name}")
        logger.info(f"Laps: {self.state.current_lap}/{self.state.total_laps}")
        logger.info(f"Drivers: {len(self.state.drivers)}")
        logger.info(f"Safety Cars: {self.state.safety_car_count}")
        logger.info(f"Virtual Safety Cars: {self.state.virtual_safety_car_count}")
        logger.info(f"Red Flags: {self.state.red_flag_count}")
        logger.info(f"Race Control Events: {len(self.state.race_control_events)}")
        logger.info(f"Total Pitstops: {sum(len(driver.pitstops) for driver in self.state.drivers.values())}")
        logger.info("="*60)