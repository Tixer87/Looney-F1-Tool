import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .state import LiveSessionState,LiveDriverState
logger=logging.getLogger(__name__)
F1DASH_TEAM_MAP={
    "Red Bull Racing":"Red Bull",
    "Mercedes":"Mercedes",
    "Ferrari":"Ferrari",
    "McLaren":"McLaren",
    "McLaren F1 Team":"McLaren",
    "Aston Martin":"Aston Martin",
    "Alpine":"Alpine",
    "Williams":"Williams",
    "RB":"Racing Bulls",
    "Racing Bulls":"Racing Bulls",
    "Visa Cash App RB":"Racing Bulls",
    "Kick Sauber":"Sauber",
    "Sauber":"Sauber",
    "Haas F1 Team":"Haas",
    "Haas":"Haas"
}
class LiveToRLTExporter:
    def __init__(self,state:'LiveSessionState'):
        self.state=state
    def export_rlt(self)->dict:
        from export.rlt_adapter import _to_milliseconds
        from export.native_rlt import build_native_session
        from api.export_service import validate_export
        entries=[]
        for driver in self.state.drivers.values():
            entries.append({
                "Driver":{"Name":driver.full_name},
                "RaceNumber":driver.racing_number,
                "Team":{"Name":driver.team_name},
                "Position":driver.final_position or driver.current_position or len(entries)+1,
                "GridPosition":driver.grid_position,
                "Status":driver.finishing_status,
                "FastestLapTimeInt":_to_milliseconds(driver.best_laptime),
                "TimeInt":0,
                "LapsCount":driver.laps_completed,
                "PitsCount":len(driver.pitstops)
            })
        session=self.state.session_type.lower()
        payload={
            "season":self.state.year,
            "circuit":self.state.circuit_name,
            "date":self.state.session_date.isoformat() if self.state.session_date else None,
            "session_type":"Qualification" if "qual" in session else "Practice" if "practice" in session else "Race",
            "race_type":"Sprint" if "sprint" in session else "Regular",
            "is_live":True,
            "total_laps":self.state.total_laps,
            "Drivers":entries,
            "safety_car_count":self.state.safety_car_count,
            "virtual_safety_car_count":self.state.virtual_safety_car_count
        }
        result=build_native_session(payload)
        validate_export(result)
        return result
    def export(self)->dict:
        logger.info("Generating RLT export")
        drivers=[self._build_driver_block(driver) for driver in self.state.drivers.values()]
        drivers.sort(key=lambda driver:driver.get("EndPosition",999))
        logger.info(f"Export complete: {len(drivers)} drivers")
        return {"Meta":self._build_meta(),"Drivers":drivers}
    def _build_meta(self)->dict:
        return {
            "Event":self.state.event_name,
            "Track":self.state.circuit_name,
            "Year":self.state.year,
            "Session":self.state.session_type,
            "Date":self.state.session_date.isoformat() if self.state.session_date else "",
            **({"Weather":{"AirTemp":self.state.weather.air_temp,"TrackTemp":self.state.weather.track_temp,"Rainfall":self.state.weather.rainfall}} if self.state.weather else {}),
            "RaceControl":{"SafetyCar":self.state.safety_car_count,"VSC":self.state.virtual_safety_car_count,"RedFlag":self.state.red_flag_count}
        }
    def _build_driver_block(self,driver:'LiveDriverState')->dict:
        return {
            "Name":driver.full_name,
            "Number":driver.racing_number,
            "Team":self._map_team_name(driver.team_name),
            "Nation":driver.country_code or "UNK",
            "StartPosition":driver.grid_position,
            "EndPosition":driver.final_position or driver.current_position,
            "Laps":driver.laps_completed,
            "Status":driver.finishing_status,
            "BestLaptime":driver.best_laptime,
            "Pitstops":[{"Lap":stop.lap,"Compound":stop.compound_out,"StopCount":stop.stop_number} for stop in driver.pitstops]
        }
    def _map_team_name(self,team_name:str)->str:
        if team_name in F1DASH_TEAM_MAP:return F1DASH_TEAM_MAP[team_name]
        try:
            from mapping.teams_aliases import get_team_name
            team=get_team_name(team_name,year=self.state.year)
            if team and team.get("Name")!="Unknown Team":return team["Name"]
        except Exception as exc:
            logger.debug(f"team_aliases lookup failed: {exc}")
        cleaned=team_name.replace(" F1 Team","").replace(" Racing","").strip()
        logger.warning(f"Team not in live map: {team_name}, using cleaned: {cleaned}")
        return cleaned