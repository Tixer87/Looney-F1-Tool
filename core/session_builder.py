from api.jolpica_api import fetch_race_data
from mapping.circuit_aliases import get_circuit
from mapping.drivers_aliases import get_driver_by_name
from utils.logging_setup import get_logger
log=get_logger(__name__)
def _results(race_data,session_type):
    mode=session_type.lower()
    if mode=="sprint" and "SprintResults" in race_data:return race_data["SprintResults"]
    if mode=="qualifying" and "QualifyingResults" in race_data:return race_data["QualifyingResults"]
    return race_data.get("Results",[])
def _driver_name(driver):
    return " ".join(x for x in (driver.get("givenName",""),driver.get("familyName","")) if x).strip()
def get_driver_name(full_name:str,year:int=2025)->dict:
    driver=get_driver_by_name(full_name,year)
    name=driver["Name"] if driver else full_name
    return {"Name":name,"InGameName":name}
def build_session_metadata(year,round_number,session_type="results"):
    log.debug("Building session metadata: year=%s, round=%s, session_type=%s",year,round_number,session_type)
    data=fetch_race_data(year,round_number,session_type)
    races=data.get("MRData",{}).get("RaceTable",{}).get("Races",[])
    if not races:
        log.warning("No race data found: year=%s, round=%s, session_type=%s",year,round_number,session_type)
        return {}
    race=races[0]
    results=_results(race,session_type)
    if not results:
        log.warning("No results block found: year=%s, round=%s, session_type=%s",year,round_number,session_type)
        return {}
    fastest=results[0].get("FastestLap",{})
    fastest_time=fastest.get("Time",{}).get("time","0:00.000")
    fastest_time_int=int(fastest_time.replace(":","").replace(".","")) if fastest_time else 0
    circuit_raw=race.get("Circuit",{})
    try:track_name,track_unique=get_circuit(circuit_raw)
    except ValueError:
        track_name=circuit_raw.get("circuitName","Unknown")
        track_unique="unknown.track"
    return {
        "SessionType":session_type.capitalize(),
        "RaceType":"Regular",
        "QualType":"Regular",
        "SessionStatus":"FullPoints",
        "SessionPosition":int(race.get("round",0)),
        "FastestLapTimeInt":fastest_time_int,
        "FastestLapNumLap":int(fastest.get("lap",0)),
        "TrackName":track_name,
        "TrackUniqueName":track_unique,
        "IsLiveData":False,
        "LiveRecordPercent":0,
        "IsLiveFullRecord":False,
        "IsSingleplayerMode":False,
        "WeatherType":"Clear",
        "AirTemperature":0,
        "TrackTemperature":0,
        "TotalLaps":int(results[0].get("laps",0)),
        "SessionDuration":"00:00:00"
    }
def map_driver_data(driver_data,api_driver_result=None):
    result=api_driver_result or {}
    raw=result.get("Driver",{})
    nationality=raw.get("nationality","")
    block={"Driver":{"Name":driver_data["Name"],"InGameName":driver_data.get("InGameName",driver_data["Name"])},"RaceNumber":int(result.get("number",0) or 0)}
    if nationality:block["Driver"]["_nationality_raw"]=nationality
    return block
def build_driver_blocks(year,round_number,session_type="results",quali_phase=None):
    data=fetch_race_data(year,round_number,session_type)
    races=data.get("MRData",{}).get("RaceTable",{}).get("Races",[])
    if not races:return []
    results=_results(races[0],session_type)
    blocks=[]
    for result in results:
        if session_type.lower()=="qualifying" and quali_phase and result.get(quali_phase) is None:continue
        name=_driver_name(result.get("Driver",{}))
        block=map_driver_data(get_driver_name(name,year),result)
        if session_type.lower()=="qualifying" and quali_phase:block[quali_phase]=result[quali_phase]
        blocks.append(block)
    return blocks