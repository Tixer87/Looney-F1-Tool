"""
Exporter
Exportiert Live Session State zu RLT JSON
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import LiveSessionState, LiveDriverState

logger = logging.getLogger(__name__)


class LiveToRLTExporter:
    """Exportiert Live Session State zu RLT JSON"""
    
    def __init__(self, state: 'LiveSessionState'):
        self.state = state
    
    def export(self) -> dict:
        """
        Generiere RLT-kompatibles JSON
        
        Returns:
            dict: RLT JSON Structure
        """
        logger.info("Generating RLT export")
        
        # Meta Block
        meta = self._build_meta()
        
        # Driver Blocks
        drivers = []
        for driver_state in self.state.drivers.values():
            driver_block = self._build_driver_block(driver_state)
            drivers.append(driver_block)
        
        # Sort by final position
        drivers.sort(key=lambda d: d.get("EndPosition", 999))
        
        logger.info(f"Export complete: {len(drivers)} drivers")
        
        return {
            "Meta": meta,
            "Drivers": drivers
        }
    
    def _build_meta(self) -> dict:
        """Meta Block aus Live State"""
        """Meta Block aus Live State"""
        return {
            "Event": self.state.event_name,
            "Track": self.state.circuit_name,
            "Year": self.state.year,
            "Session": self.state.session_type,
            "Date": self.state.session_date.isoformat() if self.state.session_date else "",
            # Weather (Optional, nur wenn vorhanden)
            **({"Weather": {
                "AirTemp": self.state.weather.air_temp,
                "TrackTemp": self.state.weather.track_temp,
                "Rainfall": self.state.weather.rainfall
            }} if self.state.weather else {}),
            "RaceControl": {
                "SafetyCar": self.state.safety_car_count,
                "VSC": self.state.virtual_safety_car_count,
                "RedFlag": self.state.red_flag_count
            }
        }
    
    def _build_driver_block(self, driver: 'LiveDriverState') -> dict:
        """
        Driver Block aus Live Driver State
        
        Args:
            driver: Live Driver State
            
        Returns:
            dict: RLT Driver Block
        """
        
        # Mappings anwenden (via bestehende Module)
        # f1-dash liefert bereits 3-Letter Codes (NED, GBR, etc.) - direkt verwenden
        nation = driver.country_code if driver.country_code else "UNK"
        
        # Team Mapping: f1-dash liefert "Red Bull Racing", "Mercedes" etc.
        team = self._map_team_name(driver.team_name)
        
        # Driver Name: fullName direkt verwenden (bereits RLT-kompatibel)
        driver_name = driver.full_name
        
        # Pitstops Array
        pitstops = [
            {
                "Lap": ps.lap,
                "Compound": ps.compound_out,
                "StopCount": ps.stop_number
            }
            for ps in driver.pitstops
        ]
        
        return {
            "Name": driver_name,
            "Number": driver.racing_number,
            "Team": team,
            "Nation": nation,
            "StartPosition": driver.grid_position,
            "EndPosition": driver.final_position or driver.current_position,
            "Laps": driver.laps_completed,
            "Status": driver.finishing_status,
            "BestLaptime": driver.best_laptime,
            "Pitstops": pitstops
        }
    
    def _map_team_name(self, team_name: str) -> str:
        """
        Map f1-dash Team Name zu RLT Team Name
        
        f1-dash liefert: "Red Bull Racing", "Mercedes", "McLaren F1 Team" etc.
        RLT erwartet: "Red Bull", "Mercedes", "McLaren" etc.
        
        Args:
            team_name: Team Name aus f1-dash
            
        Returns:
            RLT-konformer Team Name
        """
        # Live-spezifisches Mapping für f1-dash Team Names
        F1DASH_TEAM_MAP = {
            "Red Bull Racing": "Red Bull",
            "Mercedes": "Mercedes",
            "Ferrari": "Ferrari",
            "McLaren": "McLaren",
            "McLaren F1 Team": "McLaren",
            "Aston Martin": "Aston Martin",
            "Alpine": "Alpine",
            "Williams": "Williams",
            "RB": "Racing Bulls",
            "Racing Bulls": "Racing Bulls",
            "Visa Cash App RB": "Racing Bulls",
            "Kick Sauber": "Sauber",
            "Sauber": "Sauber",
            "Haas F1 Team": "Haas",
            "Haas": "Haas",
        }
        
        # Exact match
        if team_name in F1DASH_TEAM_MAP:
            return F1DASH_TEAM_MAP[team_name]
        
        # Try get_team_name als Fallback (versucht normalize_key Matching)
        try:
            from mapping.teams_aliases import get_team_name
            team_info = get_team_name(team_name, year=self.state.year)
            if team_info and team_info.get("Name") != "Unknown Team":
                return team_info["Name"]
        except Exception as e:
            logger.debug(f"team_aliases lookup failed: {e}")
        
        # Fallback: Cleanup common suffixes
        cleaned = team_name.replace(" F1 Team", "").replace(" Racing", "").strip()
        logger.warning(f"Team not in live map: {team_name}, using cleaned: {cleaned}")
        return cleaned
