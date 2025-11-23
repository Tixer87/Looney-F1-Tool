"""
Race Control Parser
Parsed Race Control Messages für SC/VSC/Red Flag
"""

import logging
from datetime import datetime, timezone
from typing import Set, TYPE_CHECKING
from dateutil.parser import parse as parse_datetime

if TYPE_CHECKING:
    from ..state import LiveSessionState, RaceControlEvent

logger = logging.getLogger(__name__)


class RaceControlParser:
    """Parsed Race Control Messages für SC/VSC/Red Flag"""
    
    def __init__(self, state: 'LiveSessionState'):
        self.state = state
        self.processed_timestamps: Set[str] = set()  # Dedup
    
    def parse_initial_messages(self, messages: list):
        """
        Parse historische Messages beim Initial-Event
        
        Args:
            messages: Liste von Race Control Messages (direkt Messages Array oder Dict mit Messages key)
        """
        # Falls messages ein dict ist mit "Messages" key (initial event format)
        if isinstance(messages, dict):
            messages_list = messages.get("Messages", messages.get("messages", []))
        else:
            messages_list = messages
            
        for msg in messages_list:
            timestamp = msg.get("Utc", msg.get("utc"))
            if timestamp not in self.processed_timestamps:
                self._parse_message(msg)
                self.processed_timestamps.add(timestamp)
    
    def parse_new_messages(self, messages: list):
        """
        Parse neue Messages aus Updates
        
        Args:
            messages: Liste von Race Control Messages
        """
        for msg in messages:
            timestamp = msg.get("Utc", msg.get("utc"))
            if timestamp not in self.processed_timestamps:
                self._parse_message(msg)
                self.processed_timestamps.add(timestamp)
    
    def _parse_message(self, msg: dict):
        """
        Parse einzelne Message
        
        Args:
            msg: Race Control Message Dict
        """
        from ..state import RaceControlEvent
        
        category = msg.get("Category", msg.get("category", "Other"))
        message_text = msg.get("Message", msg.get("message", ""))
        utc_timestamp = msg.get("Utc", msg.get("utc", ""))
        flag = msg.get("Flag", msg.get("flag"))
        
        # Auto-detect category from message wenn nicht gesetzt
        if category == "Other" and message_text:
            if "SAFETY CAR" in message_text.upper():
                category = "SafetyCar"
            elif "RED FLAG" in message_text.upper() or flag == "RED":
                category = "Flag"
        
        event = RaceControlEvent(
            timestamp=self._parse_timestamp(utc_timestamp) if utc_timestamp else datetime.now(),
            lap=msg.get("Lap", msg.get("lap", 0)),
            category=category,
            message=message_text,
            flag=flag,
            scope=msg.get("Scope", msg.get("scope"))
        )
        self.state.race_control_events.append(event)
        
        # Count SC/VSC/Red Flag
        if category == "SafetyCar":
            if "SAFETY CAR" in message_text.upper() and "VIRTUAL" not in message_text.upper():
                self.state.safety_car_count += 1
                logger.info(f"Safety Car deployed (Total: {self.state.safety_car_count})")
            elif "VIRTUAL SAFETY CAR" in message_text.upper():
                self.state.virtual_safety_car_count += 1
                logger.info(f"Virtual Safety Car deployed (Total: {self.state.virtual_safety_car_count})")
        
        if flag == "RED" or "RED FLAG" in message_text.upper():
            self.state.red_flag_count += 1
            logger.info(f"Red Flag (Total: {self.state.red_flag_count})")
    
    def _parse_timestamp(self, utc_str: str) -> datetime:
        """
        Parse UTC Timestamp String
        
        Args:
            utc_str: UTC Timestamp String
            
        Returns:
            datetime: Parsed datetime object
        """
        try:
            return parse_datetime(utc_str)
        except Exception as e:
            logger.error(f"Failed to parse timestamp '{utc_str}': {e}")
            from datetime import timezone as tz
            return datetime.now(tz.utc)
