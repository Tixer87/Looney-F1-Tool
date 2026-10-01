from api.jolpica_api import fetch_race_data,fetch_pitstops_data
from core.helpers import time_as_int
from mapping.teams_aliases import get_team_name
DEFAULT_FASTEST_LAP_FLAGS=15
def get_team_data(constructor_id:str,year:int)->dict:
    if not constructor_id:return {"Name":"Unknown Team","UniqueName":"Unknown","Abbr":"UNK"}
    return get_team_name({"constructorId":constructor_id},year)
def parse_stints_for_driver(pitstops:list,total_laps:int):
    stints=[]
    compounds=[]
    prev_lap=1
    for stop in pitstops:
        lap=int(stop["lap"])
        stints.append(f"X{lap-prev_lap}")
        compounds.append("Unknown")
        prev_lap=lap
    stints.append(f"X{total_laps-prev_lap+1}")
    compounds.append("Unknown")
    return ",".join(stints),len(stints),compounds
def _driver_name(result):
    driver=result.get("Driver",{})
    return " ".join(x for x in (driver.get("givenName",""),driver.get("familyName","")) if x).strip()
def _base_driver(result,team_data):
    driver=result.get("Driver",{})
    name=_driver_name(result)
    return {
        "Driver":{"Name":name,"InGameName":name,"_nationality_raw":driver.get("nationality","")},
        "RaceNumber":int(result.get("number",0) or 0),
        "Team":{"Name":team_data["Name"],"UniqueName":team_data["UniqueName"],"_constructorId":result.get("Constructor",{}).get("constructorId","")},
        "SeatType":"Primary",
        "PenaltySecsIngame":0,
        "PenaltyPosIngame":0,
        "PenaltySecsStewards":0,
        "PenaltyPosStewards":0,
        "PenaltyPoints":0,
        "DriverPointsRaw":0,
        "TeamPointsRaw":0
    }
def build_driver_block(driver_result:dict,year:int,round_number:int,winner_time_ms:int)->dict:
    constructor_id=driver_result.get("Constructor",{}).get("constructorId","")
    block=_base_driver(driver_result,get_team_data(constructor_id,year))
    status_raw=driver_result.get("status","").lower()
    time_int=int(driver_result.get("Time",{}).get("millis",0) or 0)
    fastest=driver_result.get("FastestLap",{})
    fastest_time=fastest.get("Time",{}).get("time","0:00.000")
    laps_count=int(driver_result.get("laps",0) or 0)
    pitstops=fetch_pitstops_data(year,round_number)
    driver_id=driver_result.get("Driver",{}).get("driverId","").lower()
    driver_pits=[p for p in pitstops if p.get("driverId","").lower()==driver_id]
    block.update({
        "Position":int(driver_result.get("position",0) or 0),
        "Status":"Ok" if status_raw=="finished" else "Dnf",
        "TimeInt":time_int,
        "GapInt":time_int-winner_time_ms if time_int and winner_time_ms else 0,
        "FastestLapTimeInt":time_as_int(fastest_time),
        "FastestLapNumLap":int(fastest.get("lap",0) or 0),
        "FastestLapValidFlags":0,
        "LapsCount":laps_count,
        "GridPosition":int(driver_result.get("grid",0) or 0),
        "PitsCount":len(driver_pits)
    })
    return block
def build_driver_blocks(year,round_number,session_type="results",quali_phase=None):
    data=fetch_race_data(year,round_number,session_type)
    races=data.get("MRData",{}).get("RaceTable",{}).get("Races",[])
    if not races:return []
    race_data=races[0]
    mode=session_type.lower()
    if mode=="qualifying" and "QualifyingResults" in race_data:results=race_data["QualifyingResults"]
    elif mode=="sprint" and "SprintResults" in race_data:results=race_data["SprintResults"]
    else:results=race_data.get("Results",[])
    if mode=="qualifying" and quali_phase:
        blocks=[]
        max_pos=15 if quali_phase=="Q2" else 10 if quali_phase=="Q3" else 20
        for result in results:
            pos=int(result.get("position",0) or 0)
            if pos>max_pos:continue
            quali_time=result.get(quali_phase,"")
            constructor_id=result.get("Constructor",{}).get("constructorId","")
            block=_base_driver(result,get_team_data(constructor_id,year))
            time_int=time_as_int(quali_time) if quali_time else 0
            block.update({
                "Position":pos,
                "Status":"Ok",
                "TimeInt":time_int,
                "GapInt":0,
                "FastestLapTimeInt":time_int,
                "FastestLapNumLap":1,
                "FastestLapValidFlags":DEFAULT_FASTEST_LAP_FLAGS,
                "LapsCount":1,
                "GridPosition":pos,
                "PitsCount":0,
                quali_phase:quali_time or ""
            })
            blocks.append(block)
        return blocks
    winner_time_ms=int(results[0].get("Time",{}).get("millis",0) or 0) if results else 0
    return [build_driver_block(result,year,round_number,winner_time_ms) for result in results]