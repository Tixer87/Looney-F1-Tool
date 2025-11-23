"""
Main Recorder Orchestrator
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .state import LiveSessionState
from .client import F1DashClient
from .processor import LiveEventProcessor
from .exporter import LiveToRLTExporter

logger = logging.getLogger(__name__)


class LiveRecorder:
    """Orchestrator für Live Recording"""
    
    def __init__(self, f1dash_url: str, output_dir: str):
        """
        Args:
            f1dash_url: URL des f1-dash Services (z.B. http://localhost:4000)
            output_dir: Output-Verzeichnis für RLT JSON Exports
        """
        self.f1dash_url = f1dash_url
        self.output_dir = output_dir
        self.client = F1DashClient(f1dash_url)
        self.state: Optional[LiveSessionState] = None
        self.processor: Optional[LiveEventProcessor] = None
        self.finalized: bool = False
    
    def start_recording(self):
        """Start Live Recording"""
        logger.info(f"Connecting to f1-dash at {self.f1dash_url}...")
        
        # Health Check
        if not self.client.health_check():
            raise ConnectionError(f"f1-dash is not reachable at {self.f1dash_url}!")
        
        logger.info("f1-dash is healthy. Starting recording...")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Connect to SSE stream
        self.client.connect(
            on_initial=self._on_initial,
            on_update=self._on_update,
            on_error=self._on_error
        )
    
    def _on_initial(self, data: dict):
        """Initial Event Handler"""
        logger.info("Received initial state")
        
        # Initialize Session State
        self.state = self._create_session_state(data)
        self.processor = LiveEventProcessor(self.state)
        
        # Process Initial Data
        self.processor.process_initial(data)
        
        logger.info(f"Recording session: {self.state.event_name} - {self.state.session_name}")
        logger.info(f"{len(self.state.drivers)} drivers initialized")
        logger.info(f"Lap {self.state.current_lap}/{self.state.total_laps}")
    
    def _on_update(self, data: dict):
        """Update Event Handler"""
        if not self.processor or not self.state:
            return
        
        self.processor.process_update(data)
        
        # Check Session Ende
        if self.state.session_status in ["Finished", "Finalised"] and not self.finalized:
            self._finalize_recording()
    
    def _on_error(self, error: Exception):
        """Error Handler"""
        logger.error(f"Stream error: {error}")
        
        # TODO: Reconnect Logic
        # For now: Try to finalize if we have data
        if self.state and not self.finalized:
            logger.warning("Attempting to finalize session after error...")
            self._finalize_recording()
    
    def _finalize_recording(self):
        """Session beendet → Export"""
        if self.finalized:
            return
        
        self.finalized = True
        
        logger.info("Session finished. Finalizing...")
        
        if not self.state:
            logger.error("No state to finalize!")
            return
        
        self.state.freeze()
        
        # Export to RLT JSON
        exporter = LiveToRLTExporter(self.state)
        rlt_json = exporter.export()
        
        # Save to file
        filename = self._generate_filename()
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rlt_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Export saved to: {filepath}")
        
        # Print summary
        self._print_summary()
    
    def _create_session_state(self, initial_data: dict) -> LiveSessionState:
        """Erstelle initialen Session State"""
        from dateutil.parser import parse as parse_datetime
        
        session_info = initial_data.get("sessionInfo", {})
        meeting = session_info.get("meeting", {})
        
        # Parse start date
        start_date_str = session_info.get("startDate", "")
        try:
            session_date = parse_datetime(start_date_str)
            year = session_date.year
        except:
            session_date = datetime.now(timezone.utc)
            year = datetime.now(timezone.utc).year
        
        return LiveSessionState(
            session_key=session_info.get("key", 0),
            session_name=session_info.get("name", "Unknown"),
            session_type=session_info.get("type", "Unknown"),
            event_name=meeting.get("name", "Unknown"),
            circuit_key=meeting.get("circuit", {}).get("key", 0),
            circuit_name=meeting.get("circuit", {}).get("shortName", "Unknown"),
            country_name=meeting.get("country", {}).get("name", ""),
            country_code=meeting.get("country", {}).get("code", ""),
            year=year,
            session_date=session_date,
            gmt_offset=session_info.get("gmtOffset", "00:00:00")
        )
    
    def _generate_filename(self) -> str:
        """Generiere Dateinamen für Export"""
        if not self.state:
            return "unknown_session.json"
        
        # Clean event name
        event_clean = self.state.event_name.replace(" ", "_").replace("/", "-")
        session_clean = self.state.session_type.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{event_clean}_{session_clean}_{self.state.year}_{timestamp}.json"
    
    def _print_summary(self):
        """Print Recording Summary"""
        if not self.state:
            return
        
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
        
        # Count pitstops
        total_pitstops = sum(len(d.pitstops) for d in self.state.drivers.values())
        logger.info(f"Total Pitstops: {total_pitstops}")
        
        logger.info("="*60)
