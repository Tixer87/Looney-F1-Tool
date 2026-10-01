import logging
from datetime import datetime,timezone
from typing import Set,TYPE_CHECKING
from dateutil.parser import parse as parse_datetime
if TYPE_CHECKING:
    from ..state import LiveSessionState
logger=logging.getLogger(__name__)
class RaceControlParser:
    def __init__(self,state:'LiveSessionState'):
        self.state=state
        self.processed_timestamps:Set[str]=set()
    def parse_initial_messages(self,messages:list):
        messages_list=messages.get("Messages",messages.get("messages",[])) if isinstance(messages,dict) else messages
        for msg in messages_list:
            timestamp=msg.get("Utc",msg.get("utc"))
            if timestamp not in self.processed_timestamps:
                self._parse_message(msg)
                self.processed_timestamps.add(timestamp)
    def parse_new_messages(self,messages:list):
        for msg in messages:
            timestamp=msg.get("Utc",msg.get("utc"))
            if timestamp not in self.processed_timestamps:
                self._parse_message(msg)
                self.processed_timestamps.add(timestamp)
    def _parse_message(self,msg:dict):
        from ..state import RaceControlEvent
        category=msg.get("Category",msg.get("category","Other"))
        message_text=msg.get("Message",msg.get("message",""))
        utc_timestamp=msg.get("Utc",msg.get("utc",""))
        flag=msg.get("Flag",msg.get("flag"))
        upper=message_text.upper()
        if category=="Other" and message_text:
            if "SAFETY CAR" in upper:category="SafetyCar"
            elif "RED FLAG" in upper or flag=="RED":category="Flag"
        self.state.race_control_events.append(RaceControlEvent(
            timestamp=self._parse_timestamp(utc_timestamp) if utc_timestamp else datetime.now(),
            lap=msg.get("Lap",msg.get("lap",0)),
            category=category,
            message=message_text,
            flag=flag,
            scope=msg.get("Scope",msg.get("scope"))
        ))
        if category=="SafetyCar":
            if "SAFETY CAR" in upper and "VIRTUAL" not in upper:
                self.state.safety_car_count+=1
                logger.info(f"Safety Car deployed (Total: {self.state.safety_car_count})")
            elif "VIRTUAL SAFETY CAR" in upper:
                self.state.virtual_safety_car_count+=1
                logger.info(f"Virtual Safety Car deployed (Total: {self.state.virtual_safety_car_count})")
        if flag=="RED" or "RED FLAG" in upper:
            self.state.red_flag_count+=1
            logger.info(f"Red Flag (Total: {self.state.red_flag_count})")
    def _parse_timestamp(self,utc_str:str)->datetime:
        try:return parse_datetime(utc_str)
        except Exception as exc:
            logger.error(f"Failed to parse timestamp '{utc_str}': {exc}")
            return datetime.now(timezone.utc)