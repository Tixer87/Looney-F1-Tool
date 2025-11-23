"""
Pitstop Detector
Erkennt Boxenstopps via Stint-Changes
"""

import logging
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import LiveSessionState, LiveDriverState, PitstopData

logger = logging.getLogger(__name__)


class PitstopDetector:
    """Erkennt Boxenstopps via Stint-Changes"""
    
    def __init__(self, state: 'LiveSessionState'):
        self.state = state
        self.previous_stint_counts: Dict[str, int] = {}
    
    def initialize_stint_counts(self, timing_app_data: dict):
        """
        Initialisiere Stint-Counts beim Initial-Event (ohne Pitstops zu registrieren)
        
        Args:
            timing_app_data: timingAppData aus f1-dash Initial
        """
        lines = timing_app_data.get("Lines", timing_app_data.get("lines", {}))
        
        for number, app_data in lines.items():
            stints = app_data.get("Stints", app_data.get("stints", []))
            self.previous_stint_counts[number] = len(stints)
        
        logger.info(f"Initialized stint counts for {len(self.previous_stint_counts)} drivers")
    
    def check_stint_changes(self, timing_app_data: dict):
        """
        Prüft ob Fahrer neuen Stint begonnen haben
        
        Args:
            timing_app_data: timingAppData aus f1-dash Update
        """
        lines = timing_app_data.get("Lines", timing_app_data.get("lines", {}))
        
        for number, app_data in lines.items():
            stints = app_data.get("Stints", app_data.get("stints", []))
            current_stint_count = len(stints)
            previous_count = self.previous_stint_counts.get(number, 0)
            
            if current_stint_count > previous_count and previous_count > 0:
                # Pitstop erkannt!
                driver = self.state.drivers.get(number)
                if driver:
                    self._register_pitstop(driver, stints)
            
            self.previous_stint_counts[number] = current_stint_count
    
    def _register_pitstop(self, driver: 'LiveDriverState', stints: list):
        """
        Registriere Pitstop im Driver State
        
        Args:
            driver: Driver State
            stints: Stint-Liste aus f1-dash
        """
        from ..state import PitstopData
        
        stop_number = len(driver.pitstops) + 1
        
        # Compound In/Out
        compound_in = stints[-2].get("Compound", stints[-2].get("compound", "UNKNOWN")) if len(stints) >= 2 else "START"
        compound_out = stints[-1].get("Compound", stints[-1].get("compound", "UNKNOWN"))
        
        pitstop = PitstopData(
            stop_number=stop_number,
            lap=self.state.current_lap,
            compound_in=compound_in,
            compound_out=compound_out
        )
        driver.pitstops.append(pitstop)
        
        logger.info(f"PITSTOP: {driver.tla} - Stop {stop_number} on Lap {self.state.current_lap}: {compound_in} → {compound_out}")
