from typing import Any
from datetime import datetime,timezone
import copy
from export.rlt_enums import TYRE_TYPE_TO_NUM,TOP_LEVEL_REQUIRED,DRIVER_REQUIRED,DRIVER_REQUIRED_QUALI
from mapping.drivers_aliases import get_driver_by_name
from mapping.teams_aliases import get_team_name
from mapping.drivers_nations import get_driver_nation
from mapping.circuit_aliases import get_circuit
from utils.logging_setup import get_logger
log=get_logger(__name__)
def format_ms_short(ms:int)->str:
    if not ms or ms<0:return "0:00.000"
    s,ms_remainder=divmod(ms,1000)
    m,s=divmod(s,60)
    return f"{m}:{s:02d}.{ms_remainder:03d}"
def _has_time(driver:dict,key:str)->bool:
    value=driver.get(key)
    return bool(value and str(value).strip() not in ("","NaT","None","0"))
def _position(driver:dict)->int:
    try:return int(driver.get("Position") or driver.get("position") or 0)
    except (TypeError,ValueError):return 0
def _qual_phase_member(driver:dict,phase:str)->bool:
    if phase=="Q1":return _has_time(driver,"Q1")
    position=_position(driver)
    if phase=="Q2":return _has_time(driver,"Q2") or bool(0<position<=15 and _has_time(driver,"Q1"))
    if phase=="Q3":return _has_time(driver,"Q3") or bool(0<position<=10 and _has_time(driver,"Q2"))
    return False
def build_rlt_session(payload:dict)->dict:
    log.info(f"Building RLT session: session_type={payload.get('session_type')}")
    payload=copy.deepcopy(payload)
    session_type=_map_session_type(payload.get('session_type'))
    race_type=_map_race_type(payload.get('race_type'))
    qual_type=_map_qual_type(payload.get('qual_type')) if session_type=="Qualification" else None
    current_q_session=payload.get('_current_q_session')
    if race_type=="Main":race_type="Regular"
    session_position=payload.get('session_position',payload.get('SessionPosition',1))
    if current_q_session=='Q1':session_position=0
    elif current_q_session=='Q2':session_position=1
    elif current_q_session=='Q3':session_position=2
    circuit_raw=payload.get('circuit') or payload.get('Circuit')
    track_name,track_unique=get_circuit(circuit_raw)
    date_str=payload.get('date') or payload.get('Date')
    stamp=datetime.fromisoformat(str(date_str).replace('Z','+00:00')) if date_str else datetime.now(timezone.utc)
    if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=timezone.utc)
    date_str=stamp.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
    drivers_raw=payload.get('drivers') or payload.get('Drivers') or []
    if current_q_session:
        original_count=len(drivers_raw)
        drivers_raw=[d for d in drivers_raw if _qual_phase_member(d,current_q_session)]
        if len(drivers_raw)<original_count:
            log.info(f"Filtered {current_q_session}: {original_count} → {len(drivers_raw)} drivers")
    drivers=[]
    for driver_raw in drivers_raw:
        driver_raw['_season']=payload.get('season',payload.get('year',2025))
        driver=_build_driver(driver_raw,session_type,current_q_session)
        if driver:drivers.append(driver)
    if not drivers:log.warning("No drivers in session")
    if current_q_session and drivers:
        drivers.sort(key=lambda d:d.get('TimeInt',999999999) if d.get('TimeInt',0)>0 else 999999999)
        for idx,driver in enumerate(drivers,start=1):driver['Position']=idx
    if session_type=="Race":drivers=_calculate_gaps_race(drivers)
    elif session_type in ("Qualification","Practice"):drivers=_calculate_gaps_quali(drivers)
    result={
        "SessionType":session_type,
        "RaceType":race_type,
        "QualType":qual_type or "Regular",
        "SessionStatus":payload.get('session_status') or payload.get('SessionStatus') or "FullPoints",
        "SessionPosition":session_position,
        "Date":date_str,
        "FastestLapTimeInt":0,
        "FastestLapNumLap":0,
        "TrackName":track_name,
        "TrackUniqueName":track_unique,
        "IsLiveData":payload.get('is_live') or payload.get('IsLiveData') or False,
        "LiveRecordPercent":payload.get('live_record_percent') or payload.get('LiveRecordPercent') or 0,
        "IsLiveFullRecord":payload.get('is_live_full_record') or payload.get('IsLiveFullRecord') or False,
        "IsSingleplayerMode":payload.get('is_singleplayer') or payload.get('IsSingleplayerMode') or False,
        "WeatherType":"Clear",
        "AirTemperature":0,
        "TrackTemperature":0,
        "TotalLaps":payload.get('total_laps') or payload.get('TotalLaps') or max((d.get('LapsCount',0) for d in drivers),default=0),
        "SessionDuration":"00:00:00",
        "Drivers":drivers
    }
    if drivers:
        fastest_times=[d.get('FastestLapTimeInt',0) for d in drivers if d.get('FastestLapTimeInt',0)>0]
        if fastest_times:
            result["FastestLapTimeInt"]=min(fastest_times)
            for driver in drivers:
                if driver.get('FastestLapTimeInt')==result["FastestLapTimeInt"]:
                    result["FastestLapNumLap"]=driver.get('FastestLapNumLap',0)
                    break
    if 'weather' in payload or 'WeatherType' in payload:
        weather=_map_weather(payload.get('weather') or payload.get('WeatherType'))
        if weather:result["WeatherType"]=weather
    if 'air_temp' in payload or 'AirTemperature' in payload:result["AirTemperature"]=int(payload.get('air_temp') or payload.get('AirTemperature') or 0)
    if 'track_temp' in payload or 'TrackTemperature' in payload:result["TrackTemperature"]=int(payload.get('track_temp') or payload.get('TrackTemperature') or 0)
    if 'session_duration' in payload or 'SessionDuration' in payload:result["SessionDuration"]=payload.get('session_duration') or payload.get('SessionDuration') or "00:00:00"
    _validate_required_fields(result)
    log.info(f"RLT session built: {len(drivers)} drivers, track={track_name}")
    return result
def _build_driver(driver_raw:dict,session_type:str="Race",current_q_session:str|None=None)->dict|None:
    if not isinstance(driver_raw.get('Driver'),dict):
        raw=driver_raw
        value=raw.get('time',raw.get('Time',0))
        total=_to_milliseconds(value)
        if isinstance(value,str) and value.startswith('+'):total+=_to_milliseconds(raw.get('LeaderTime',0))
        name=raw.get('Name') or raw.get('name') or ' '.join(filter(None,[raw.get('givenName',raw.get('FirstName','')),raw.get('familyName',raw.get('LastName',''))]))
        driver_raw=dict(raw,Driver={'Name':name,'_nationality_raw':raw.get('nationality') or raw.get('Nationality') or ''},Team={'Name':raw.get('Team',''),'_constructorId':raw.get('constructorId') or raw.get('Constructor',{}).get('constructorId','')},RaceNumber=raw.get('RaceNumber',raw.get('DriverNumber',raw.get('number',raw.get('permanentNumber','')))),Position=int(raw.get('position',raw.get('Position',0))),TimeInt=total,FastestLapTimeInt=_to_milliseconds(raw.get('fastest_lap_time',raw.get('FastestLapTime',0))),LapsCount=int(raw.get('laps',raw.get('Laps',0)) or 0),Status=raw.get('status',raw.get('Status','Ok')),StintsRaw=encode_stints_raw(raw.get('stints',[])))
    if 'Driver' in driver_raw and isinstance(driver_raw['Driver'],dict):
        year=int(driver_raw.get("_season",2025))
        if 'Name' in driver_raw['Driver']:current_name=driver_raw['Driver']['Name']
        elif 'givenName' in driver_raw['Driver'] and 'familyName' in driver_raw['Driver']:current_name=f"{driver_raw['Driver']['givenName']} {driver_raw['Driver']['familyName']}".strip()
        else:current_name='Unknown Driver'
        driver_number=driver_raw.get('RaceNumber') or driver_raw.get('DriverNumber') or driver_raw.get('number') or driver_raw.get('permanentNumber')
        try:driver_number=int(driver_number) if driver_number else 0
        except (ValueError,TypeError):driver_number=0
        nationality_raw=driver_raw['Driver'].get('_nationality_raw') or driver_raw['Driver'].get('Nationality') or driver_raw['Driver'].get('nationality') or driver_raw.get('Nationality') or driver_raw.get('nationality') or ''
        constructor_id_raw=driver_raw.get('Team',{}).get('_constructorId','')
        driver_info=get_driver_by_name(current_name,year)
        if driver_info:
            canonical_name=driver_info['Name']
            team_unique_from_lineup=driver_info.get('Team')
            log.debug(f"Driver matched: {canonical_name}")
        else:
            canonical_name=current_name
            team_unique_from_lineup=None
            log.warning(f"Driver not in lineup: {canonical_name} (using preprocessed data)")
        if nationality_raw:
            nation_info=get_driver_nation(nationality_raw)
            log.debug(f"Nationality mapped: {nationality_raw} → {nation_info['Name']}")
        else:
            nation_info={"Name":"Unknown","Code":"UNK"}
            log.warning(f"No nationality data for {canonical_name}")
        if constructor_id_raw:
            team_info=get_team_name({"constructorId":constructor_id_raw},year)
            log.debug(f"Team from constructorId: {constructor_id_raw} → {team_info['Name']}")
        elif driver_raw.get('Team',{}).get('Name') or driver_raw.get('TeamName'):
            team_info=get_team_name(driver_raw.get('Team',{}).get('Name') or driver_raw.get('TeamName'),year)
        elif team_unique_from_lineup:
            team_id=team_unique_from_lineup.rsplit('.',1)[0] if '.' in team_unique_from_lineup else team_unique_from_lineup
            team_info=get_team_name({"name":team_id},year)
            log.debug(f"Team from lineup uniqueName: {team_unique_from_lineup} → {team_info['Name']}")
        else:
            team_raw=driver_raw.get('Team',{})
            team_name=team_raw.get('Name') or driver_raw.get('TeamName','Unknown Team')
            team_info=get_team_name({"name":team_name},year)
        driver_raw['Driver'].pop('_nationality_raw',None)
        if isinstance(driver_raw.get('Team'),dict):driver_raw['Team'].pop('_constructorId',None)
        driver_raw['Driver']['Name']=canonical_name
        driver_raw['Driver']['Nationality']=nation_info['Name']
        driver_raw.setdefault('Team',{})
        driver_raw['Team']['Name']=team_info['Name']
        driver_raw['Team']['UniqueName']=team_info['UniqueName']
        if 'DriverNumber' in driver_raw:driver_raw['RaceNumber']=int(driver_raw.pop('DriverNumber') or 0)
        driver_raw.pop('Abbreviation',None)
        driver_raw.pop('TeamName',None)
        driver_raw.pop('Time',None)
        driver_raw.pop('FastestLapTime',None)
        q1_raw=driver_raw.pop('Q1',None)
        q2_raw=driver_raw.pop('Q2',None)
        q3_raw=driver_raw.pop('Q3',None)
        if q1_raw:driver_raw['_q1_raw']=q1_raw
        if q2_raw:driver_raw['_q2_raw']=q2_raw
        if q3_raw:driver_raw['_q3_raw']=q3_raw
        driver_raw.get('Driver',{}).pop('givenName',None)
        driver_raw.get('Driver',{}).pop('familyName',None)
        driver_raw.setdefault('NationalityIngame',nation_info.get('Code','UNK'))
        driver_raw.setdefault('SeatType','Primary')
        driver_raw.setdefault('Car',{"Name":"","UniqueName":""})
        driver_raw.setdefault('StintsRaw',"")
        driver_raw.setdefault('FastestLapTyres',"Soft")
        driver_raw.setdefault('FastestLapNumLap',0)
        driver_raw.setdefault('FastestLapValidFlags',0)
        driver_raw.setdefault('PenaltySecsIngame',0)
        driver_raw.setdefault('PenaltyPosIngame',0)
        driver_raw.setdefault('PenaltySecsStewards',0)
        driver_raw.setdefault('PenaltyPosStewards',0)
        driver_raw.setdefault('PenaltyPoints',0)
        driver_raw.setdefault('DriverPointsRaw',0)
        driver_raw.setdefault('TeamPointsRaw',0)
        if session_type=="Qualification":
            driver_raw['Status']="Ok"
            q1_raw=driver_raw.pop('_q1_raw',None)
            q2_raw=driver_raw.pop('_q2_raw',None)
            q3_raw=driver_raw.pop('_q3_raw',None)
            q1_ms=_to_milliseconds(q1_raw) if q1_raw else 0
            q2_ms=_to_milliseconds(q2_raw) if q2_raw else 0
            q3_ms=_to_milliseconds(q3_raw) if q3_raw else 0
            if current_q_session=='Q1':
                driver_raw['TimeInt']=q1_ms
                driver_raw['FastestLapTimeInt']=q1_ms
                driver_raw.pop('Q1',None);driver_raw.pop('Q2',None);driver_raw.pop('Q3',None)
            elif current_q_session=='Q2':
                driver_raw['TimeInt']=q2_ms
                driver_raw['FastestLapTimeInt']=q2_ms
                driver_raw.pop('Q1',None);driver_raw.pop('Q2',None);driver_raw.pop('Q3',None)
            elif current_q_session=='Q3':
                driver_raw['TimeInt']=q3_ms
                driver_raw['FastestLapTimeInt']=q3_ms
                driver_raw.pop('Q1',None);driver_raw.pop('Q2',None);driver_raw.pop('Q3',None)
            else:
                best_time_ms=min((t for t in (q1_ms,q2_ms,q3_ms) if t>0),default=0)
                driver_raw['TimeInt']=best_time_ms or driver_raw.get('TimeInt',0)
                driver_raw['Q1']=format_ms_short(q1_ms) if q1_ms>0 else "0:00.000"
                if q2_ms>0:driver_raw['Q2']=format_ms_short(q2_ms)
                if q3_ms>0:driver_raw['Q3']=format_ms_short(q3_ms)
        if 'TimeInt' not in driver_raw or driver_raw['TimeInt']==0:driver_raw['TimeInt']=driver_raw.get('FastestLapTimeInt',0) if session_type!='Race' else 0
        if session_type!='Race' and ('FastestLapTimeInt' not in driver_raw or driver_raw['FastestLapTimeInt']==0):driver_raw['FastestLapTimeInt']=driver_raw.get('TimeInt',0)
        driver={
            "Driver":{"Name":canonical_name,"InGameName":canonical_name,"Nationality":nation_info['Name']},
            "RaceNumber":driver_number,
            "Position":int(driver_raw.get('Position',0)),
            "Team":{"Name":team_info['Name'],"UniqueName":team_info['UniqueName']},
            "SeatType":driver_raw.get('SeatType','Primary'),
            "Status":_map_driver_status(driver_raw.get('Status','Ok')),
            "TimeInt":driver_raw.get('TimeInt',0),
            "GapInt":driver_raw.get('GapInt',0),
            "FastestLapTimeInt":driver_raw.get('FastestLapTimeInt',0),
            "FastestLapNumLap":driver_raw.get('FastestLapNumLap',0),
            "FastestLapValidFlags":driver_raw.get('FastestLapValidFlags',0),
            "StintsRaw":driver_raw.get('StintsRaw',''),
            "PenaltySecsIngame":driver_raw.get('PenaltySecsIngame',0),
            "PenaltyPosIngame":driver_raw.get('PenaltyPosIngame',0),
            "PenaltySecsStewards":driver_raw.get('PenaltySecsStewards',0),
            "PenaltyPosStewards":driver_raw.get('PenaltyPosStewards',0),
            "PenaltyPoints":driver_raw.get('PenaltyPoints',0),
            "DriverPointsRaw":driver_raw.get('DriverPointsRaw',0),
            "TeamPointsRaw":driver_raw.get('TeamPointsRaw',0),
            "LapsCount":driver_raw.get('LapsCount',0),
            "GridPosition":int(driver_raw.get('GridPosition') or 0),
            "PitsCount":driver_raw.get('PitsCount',0)
        }
        if session_type=="Qualification":
            driver['Status']="Ok"
            if 'Q1' in driver_raw:driver['Q1']=driver_raw['Q1']
            if 'Q2' in driver_raw:driver['Q2']=driver_raw['Q2']
            if 'Q3' in driver_raw:driver['Q3']=driver_raw['Q3']
        return driver
    position=driver_raw.get('position') or driver_raw.get('Position')
    if not position:
        log.error(f"Driver missing position: {driver_raw}")
        return None
    try:position=int(position)
    except (ValueError,TypeError):
        log.error(f"Invalid position value: {position}")
        return None
    year=int(driver_raw.get('_season',2025))
    driver_info=None
    name_candidates=[
        driver_raw.get('name'),
        driver_raw.get('Name'),
        f"{driver_raw.get('FirstName','')} {driver_raw.get('LastName','')}".strip(),
        f"{driver_raw.get('Driver',{}).get('givenName','')} {driver_raw.get('Driver',{}).get('familyName','')}".strip()
    ]
    for name_candidate in name_candidates:
        if name_candidate:
            driver_info=get_driver_by_name(name_candidate,year)
            if driver_info:break
    if driver_info:
        driver_name=driver_info['Name']
        log.debug(f"Driver matched: {driver_name}")
    else:
        driver_name=next((name for name in name_candidates if name),"Unknown Driver")
        log.warning(f"Driver not in lineup: {driver_name} (using raw data)")
    driver_number=driver_raw.get('number') or driver_raw.get('DriverNumber') or driver_raw.get('RaceNumber') or driver_raw.get('permanentNumber')
    try:driver_number=int(driver_number) if driver_number else 0
    except (ValueError,TypeError):driver_number=0
    nationality_raw=driver_raw.get('nationality') or driver_raw.get('Nationality') or driver_raw.get('Driver',{}).get('nationality') or driver_raw.get('Driver',{}).get('Nationality')
    constructor_dict=driver_raw.get('Constructor',{})
    constructor_id=constructor_dict.get('constructorId')
    if constructor_id:team_info=get_team_name({"constructorId":constructor_id},year)
    elif driver_raw.get('Team'):team_info=get_team_name(driver_raw.get('Team'),year)
    else:team_info={"Name":"Unknown Team","UniqueName":"Unknown","Abbr":"UNK"}
    nation_info=get_driver_nation(nationality_raw) if nationality_raw else {"Name":"Unknown","Code":"UNK"}
    time_str=driver_raw.get('time') or driver_raw.get('Time') or ""
    if not time_str:
        q3_raw=driver_raw.get('_q3_raw') or ""
        q2_raw=driver_raw.get('_q2_raw') or ""
        q1_raw=driver_raw.get('_q1_raw') or ""
        time_str=q3_raw or q2_raw or q1_raw
    leader_time_str=driver_raw.get('LeaderTime') or ""
    if isinstance(time_str,str) and time_str.startswith('+') and leader_time_str:time_int=_to_milliseconds(leader_time_str)+_to_milliseconds(time_str.lstrip('+'))
    else:time_int=_to_milliseconds(time_str)
    fastest_lap_time=_to_milliseconds(driver_raw.get('fastest_lap_time') or driver_raw.get('FastestLapTime'))
    laps=driver_raw.get('laps') or driver_raw.get('Laps') or 0
    try:laps=int(laps)
    except (ValueError,TypeError):laps=0
    stints_raw_str=encode_stints_raw(driver_raw.get('stints') or driver_raw.get('Stints') or [])
    status=_map_driver_status(driver_raw.get('status') or driver_raw.get('Status'))
    seat_type=_map_seat_type(driver_raw.get('seat_type'))
    driver={
        "Driver":{"Name":driver_name,"InGameName":driver_name,"Nationality":nation_info["Name"]},
        "RaceNumber":driver_number,
        "Position":position,
        "Team":{"Name":team_info['Name'],"UniqueName":team_info['UniqueName']},
        "SeatType":seat_type or "Primary",
        "Status":status,
        "TimeInt":time_int,
        "GapInt":0,
        "FastestLapTimeInt":fastest_lap_time,
        "FastestLapNumLap":0,
        "FastestLapValidFlags":0,
        "StintsRaw":stints_raw_str,
        "PenaltySecsIngame":0,
        "PenaltyPosIngame":0,
        "PenaltySecsStewards":0,
        "PenaltyPosStewards":0,
        "PenaltyPoints":0,
        "DriverPointsRaw":0,
        "TeamPointsRaw":0,
        "LapsCount":laps,
        "GridPosition":int(driver_raw.get('grid_position') or driver_raw.get('GridPosition') or position),
        "PitsCount":driver_raw.get('pits') or driver_raw.get('PitsCount') or 0
    }
    if session_type=="Qualification":
        driver['Status']="Ok"
        q1_ms=_to_milliseconds(driver_raw.get('Q1') or "")
        q2_ms=_to_milliseconds(driver_raw.get('Q2') or "")
        q3_ms=_to_milliseconds(driver_raw.get('Q3') or "")
        driver['Q1']=format_ms_short(q1_ms) if q1_ms>0 else format_ms_short(driver['TimeInt']) if driver.get('TimeInt',0)>0 else "0:00.000"
        if q2_ms>0:driver['Q2']=format_ms_short(q2_ms)
        if q3_ms>0:driver['Q3']=format_ms_short(q3_ms)
    if driver['TimeInt']==0 and driver.get('FastestLapTimeInt',0)>0:driver['TimeInt']=driver['FastestLapTimeInt']
    if driver.get('FastestLapTimeInt',0)==0 and driver['TimeInt']>0:driver['FastestLapTimeInt']=driver['TimeInt']
    return driver
def encode_stints_raw(stints:list[dict])->str:
    if not stints:return ""
    encoded=[]
    for stint in stints:
        tyre_type=stint.get('tyre_type')
        if tyre_type is None:tyre_type=stint.get('TyreType')
        if isinstance(tyre_type,str):
            tyre_num=TYRE_TYPE_TO_NUM.get(tyre_type)
            if tyre_num is None:
                log.warning(f"Unknown tyre type in stint: {tyre_type}")
                continue
        elif isinstance(tyre_type,int):tyre_num=tyre_type
        else:
            log.warning(f"Invalid tyre type in stint: {tyre_type}")
            continue
        laps=stint.get('laps')
        if laps is None:laps=stint.get('Laps')
        try:laps=int(laps or 0)
        except (ValueError,TypeError):laps=0
        wear_start=stint.get('wear_start')
        if wear_start is None:wear_start=stint.get('WearStart')
        wear_end=stint.get('wear_end')
        if wear_end is None:wear_end=stint.get('WearEnd')
        wear_start_str=str(int(wear_start)) if wear_start is not None else ""
        wear_end_str=str(int(wear_end)) if wear_end is not None else ""
        encoded.append(f"{tyre_num}:{laps}:{wear_start_str}:{wear_end_str}")
    return ",".join(encoded)
def _calculate_gaps_race(drivers:list[dict])->list[dict]:
    if not drivers:return drivers
    drivers=sorted(drivers,key=lambda d:d.get('Position',999))
    leader=drivers[0]
    leader_time=leader.get('TimeInt',0)
    leader_laps=leader.get('LapsCount',leader.get('Laps',0))
    leader['GapInt']=0
    for driver in drivers[1:]:
        driver_time=driver.get('TimeInt',0)
        driver_laps=driver.get('LapsCount',driver.get('Laps',0))
        driver['GapInt']=max(0,driver_time-leader_time) if driver_laps==leader_laps and driver_time>0 and leader_time>0 else 0
        _validate_gap_not_lap_time(driver)
    return drivers
def _calculate_gaps_quali(drivers:list[dict])->list[dict]:
    if not drivers:return drivers
    drivers=sorted(drivers,key=lambda d:d.get('Position',999))
    pole=drivers[0]
    pole_time=pole.get('FastestLapTimeInt') or pole.get('TimeInt') or 0
    pole['GapInt']=0
    for driver in drivers[1:]:
        driver_time=driver.get('FastestLapTimeInt') or driver.get('TimeInt') or 0
        driver['GapInt']=max(0,driver_time-pole_time) if driver_time>0 and pole_time>0 else 0
    return drivers
def _validate_gap_not_lap_time(driver:dict)->None:
    gap=driver.get('GapInt',0)
    lap_time=driver.get('FastestLapTimeInt',0)
    position=driver.get('Position',0)
    if position>1 and gap>0 and lap_time>0 and abs(gap-lap_time)<=2:
        name=driver.get('Driver',{}).get('Name',driver.get('Name','Unknown'))
        msg=f"CRITICAL BUG: Driver at position {position} has GapInt={gap} equal to FastestLapTimeInt={lap_time}. GapInt should be time behind leader, not lap time!"
        log.error(f"{msg} [driver={name}, position={position}, gap={gap}, lap_time={lap_time}]")
        raise AssertionError(msg)
def _validate_required_fields(result:dict)->None:
    session_type=result.get('SessionType')
    missing=[field for field in TOP_LEVEL_REQUIRED if field not in result]
    if missing:raise ValueError(f"Missing required top-level fields: {', '.join(missing)}")
    drivers=result.get('Drivers',[])
    if not drivers:return
    is_split=result.get('QualType') in ('Q1','Q2','Q3')
    required=DRIVER_REQUIRED_QUALI if session_type=="Qualification" and not is_split else DRIVER_REQUIRED
    missing=[field for field in required if field not in drivers[0]]
    if missing:raise ValueError(f"Missing required driver fields: {', '.join(missing)}")
    if session_type=="Qualification" and not is_split:
        for index,driver in enumerate(drivers,1):
            if 'Q1' not in driver:raise ValueError(f"Driver at position {index} missing Q1 field")
            if not isinstance(driver['Q1'],str) or ':' not in driver['Q1']:raise ValueError(f"Driver at position {index} has invalid Q1 format: {driver['Q1']}")
def _to_milliseconds(value:Any)->int:
    if value is None:return 0
    if isinstance(value,int):return max(0,value)
    if isinstance(value,float):return max(0,int(value*1000))
    if isinstance(value,str):
        value=value.strip()
        if not value or value in ('DNF','DSQ','DNS'):return 0
        if 'days' in value:
            try:
                days,time_part=value.split('days',1)
                hours,minutes,seconds=time_part.strip().split(':')
                return max(0,int((int(days.strip())*86400+int(hours)*3600+int(minutes)*60+float(seconds))*1000))
            except (ValueError,IndexError):return 0
        try:return max(0,int(float(value)*1000))
        except ValueError:pass
        if ':' in value:
            try:
                parts=value.split(':')
                if len(parts)==3:return max(0,int((int(parts[0])*3600+int(parts[1])*60+float(parts[2]))*1000))
                if len(parts)==2:return max(0,int((int(parts[0])*60+float(parts[1]))*1000))
            except (ValueError,IndexError):pass
    return 0
def _map_session_type(value:Any)->str:
    if not value:return "Race"
    value=str(value).lower()
    if 'race' in value:return "Race"
    if 'qual' in value:return "Qualification"
    if 'practice' in value or 'fp' in value:return "Practice"
    return "Race"
def _map_race_type(value:Any)->str:
    if not value:return "Main"
    value=str(value).lower()
    if 'sprint' in value:return "Sprint"
    if 'feature' in value:return "Feature"
    if 'main' in value:return "Main"
    if 'first' in value or value=='1':return "First"
    if 'second' in value or value=='2':return "Second"
    if 'third' in value or value=='3':return "Third"
    return "Main"
def _map_qual_type(value:Any)->str:
    if not value:return "Regular"
    value=str(value).lower()
    if 'q1' in value:return "Q1"
    if 'q2' in value:return "Q2"
    if 'q3' in value:return "Q3"
    if 'q4' in value:return "Q4"
    return "Regular"
def _map_weather(value:Any)->str|None:
    if not value:return None
    value=str(value).lower()
    if 'storm' in value:return "Storm"
    if 'heavy' in value and 'rain' in value:return "HeavyRain"
    if 'light' in value and 'rain' in value:return "LightRain"
    if 'rain' in value or 'wet' in value:return "LightRain"
    if 'overcast' in value:return "Overcast"
    if 'cloud' in value:return "LightCloud"
    if 'clear' in value or 'sunny' in value:return "Clear"
    return None
def _map_driver_status(value:Any)->str:
    if not value:return "Ok"
    value=str(value).lower()
    if 'dnf' in value or 'retired' in value or value=='ret':return "Dnf"
    if 'dsq' in value or 'disqualified' in value:return "Dsq"
    if 'dns' in value or 'dnq' in value:return "Dns"
    return "Ok"
def _map_seat_type(value:Any)->str|None:
    if not value:return None
    value=str(value).lower()
    if 'reserve' in value:return "Reserve"
    if 'test' in value:return "TestDriver"
    return None