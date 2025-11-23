"""
Lap Completion Detector
Erkennt Runden-Abschluss und extrahiert Lap Data
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import LiveSessionState, LapData

logger = logging.getLogger(__name__)


class LapCompletionDetector:
    """Erkennt Runden-Abschluss und extrahiert Lap Data"""
    
    def __init__(self, state: 'LiveSessionState'):
        self.state = state
    
    def on_lap_change(self, new_lap: int):
        """
        Wird aufgerufen wenn current_lap sich ändert
        
        Args:
            new_lap: Neue Rundenzahl
        """
        logger.info(f"Lap {new_lap} started")
        
        # Für alle Fahrer: Lap Data speichern
        from ..state import LapData
        
        for driver in self.state.drivers.values():
            # Skip retired/stopped drivers
            if driver.retired or driver.stopped:
                continue
            
            if driver.last_laptime:
                # Lap Number: Der neue Lap ist gestartet, also ist new_lap die Nummer des abgeschlossenen Laps
                lap_data = LapData(
                    lap_number=new_lap,
                    laptime=driver.last_laptime,
                    sector_1=driver.best_sectors[0],
                    sector_2=driver.best_sectors[1],
                    sector_3=driver.best_sectors[2],
                    position=driver.current_position,
                    gap_to_leader="0.0"  # TODO: Aus timingData extrahieren
                )
                driver.lap_history.append(lap_data)
                driver.laps_completed += 1
