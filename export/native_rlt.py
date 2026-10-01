import json
import re
from datetime import datetime,timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from uuid import uuid4
from export.rlt_adapter import build_rlt_session
from mapping.circuit_aliases import get_circuit,get_circuit_by_unique
ROOT=Path(__file__).resolve().parents[1]
LAP_GAP_MS=1_000_000_000
@lru_cache(maxsize=None)
def _data(name):
    return json.loads((ROOT/'mapping'/name).read_text(encoding='utf-8'))
def time_text(ms):
    minutes,rest=divmod(int(ms),60000)
    seconds,millis=divmod(rest,1000)
    return f'{minutes}:{seconds:02d}.{millis:03d}'
def _pair(target,label,value):
    if value and value>0:
        target[label]=time_text(value)
        target[label+'Ms']=int(value)
def _gap(laps,milliseconds):
    if laps>0:return f'+{laps} '+('Lap' if laps==1 else 'Laps'),laps*LAP_GAP_MS
    if milliseconds is None:return None
    return ('0' if milliseconds==0 else f'+{milliseconds/1000:.3f}'),int(milliseconds)
def _team(team):
    result={'name':team['Name'],'uniqueId':team['UniqueName']}
    for source,target in [('FullName','fullName'),('Abbreviation','abbreviation'),('Nationality','country')]:
        if team.get(source):result[target]=team[source]
    for source,target in [('Color','primaryColor'),('SecondaryColor','secondaryColor'),('TertiaryColor','tertiaryColor')]:
        if team.get(source):
            color=str(team[source])
            if ',' in color:color='#FF'+''.join(f'{int(x):02X}' for x in color.split(','))
            result[target]=color
    return result
def _status(raw,normalized):
    value=str(raw.get('Status',normalized)).strip().lower()
    if value in ('dsq','disqualified'):return 'DSQ'
    if value in ('dns','dnq','did not start','withdrawn','withdrew'):return 'DNS'
    if value in ('ok','finished','lapped') or re.fullmatch(r'\+\d+ laps?',value):return 'Finished'
    return 'DNF'
def build_native_session(payload):
    normalized=build_rlt_session(payload)
    year=int(payload.get('season') or payload.get('year'))
    calendar=payload.get('calendar') or _data('fallback_calendars.json').get(str(year),[])
    round_no=payload.get('round')
    if not round_no:
        candidates=[e for e in calendar if get_circuit(e['location'])[1]==normalized['TrackUniqueName']]
        if len(candidates)!=1:raise ValueError('A verified season round is required for native RLT export')
        round_no=candidates[0]['round']
    round_no=int(round_no)
    event=next((e for e in calendar if int(e['round'])==round_no),{})
    event_date=event.get('date',normalized['Date'][:10])[:10]
    circuit=get_circuit_by_unique(normalized['TrackUniqueName'])
    if not circuit:raise ValueError(f"Unknown circuit UniqueName: {normalized['TrackUniqueName']}")
    race=normalized['SessionType']=='Race'
    sprint=normalized['RaceType']=='Sprint'
    phase=payload.get('_current_q_session')
    source_rows=payload.get('Drivers') or payload.get('drivers') or []
    sources={str(r.get('RaceNumber',r.get('DriverNumber',''))):r for r in source_rows}
    rows=sorted(normalized['Drivers'],key=lambda r:r['Position'])
    if not race:
        rows.sort(key=lambda r:r['FastestLapTimeInt'] or float('inf'))
        for position,row in enumerate(rows,1):row['Position']=position
    leader=rows[0] if rows else {}
    drivers=[]
    previous=None
    for row in rows:
        raw=sources.get(str(row['RaceNumber']),{})
        status=_status(raw,row['Status']) if race else 'Finished'
        unclassified=status in ('DNF','DNS','DSQ')
        driver={'driverName':row['Driver']['Name'],'driverInfo':{'raceNumber':str(row['RaceNumber']),'displayName':row['Driver']['Name']},'position':row['Position'],'classificationPosition':-1 if unclassified else row['Position'],'gridPosition':row['GridPosition'],'status':status,'lapsCompleted':row['LapsCount'],'team':_team(row['Team'])}
        nationality=row['Driver'].get('Nationality')
        if nationality and nationality.lower()!='unknown':driver['driverInfo']['nationality']=nationality
        if row['GridPosition']>0:driver['positionChange']=row['GridPosition']-row['Position']
        points=raw.get('Points')
        if points is not None:driver['driverPoints']=driver['teamPoints']=format(Decimal(str(points)).normalize(),'f')
        elif not race:driver['driverPoints']=driver['teamPoints']='0'
        if race:_pair(driver,'totalTime',row['TimeInt'])
        _pair(driver,'fastestLapTime',row['FastestLapTimeInt'])
        if not phase and row.get('FastestLapNumLap',0)>0:driver['fastestLapNumber']=row['FastestLapNumLap']
        laps_down=max(0,leader.get('LapsCount',0)-row['LapsCount']) if race else 0
        ms=row['TimeInt']-leader.get('TimeInt',0) if row['TimeInt']>0 and leader.get('TimeInt',0)>0 else None
        gap=_gap(laps_down,0 if row is leader else ms)
        if gap:driver['gap'],driver['gapMs']=gap
        if previous:
            lap_interval=max(0,previous['LapsCount']-row['LapsCount']) if race else 0
            delta=row['TimeInt']-previous['TimeInt'] if row['TimeInt']>0 and previous['TimeInt']>0 else None
            interval=_gap(lap_interval,delta if delta is not None and delta>=0 else None)
            if interval:driver['interval'],driver['intervalMs']=interval
        else:driver['interval'],driver['intervalMs']='0',0
        drivers.append(driver)
        previous=row
    session_type=normalized['SessionType']
    caption=('SQ' if sprint else 'Q')+phase[-1] if phase else ('Sprint' if sprint else 'Race') if race else payload.get('session') or session_type
    info={'sessionId':str(uuid4()),'sessionType':session_type,'sessionPosition':normalized['SessionPosition'],'sessionCaption':caption,'completedStatus':'InProgress' if payload.get('is_live') else 'Completed','sessionDate':normalized['Date'],'totalLaps':normalized['TotalLaps'],'driversCount':len(drivers)}
    if race or sprint:info['raceType']='Sprint' if sprint else 'Main'
    for source,target in [('weather_type','weatherType'),('air_temperature','airTemperature'),('track_temperature','trackTemperature'),('safety_car_count','safetyCarCount'),('virtual_safety_car_count','virtualSafetyCarCount')]:
        if payload.get(source) is not None:info[target]=payload[source]
    session={'sessionInfo':info,'drivers':drivers}
    fastest=min((r for r in rows if r['FastestLapTimeInt']>0),key=lambda r:r['FastestLapTimeInt'],default=None)
    if fastest:
        session['fastestLap']={'lapTime':time_text(fastest['FastestLapTimeInt']),'lapTimeMs':fastest['FastestLapTimeInt'],'driverName':fastest['Driver']['Name']}
        if not phase and fastest['FastestLapNumLap']>0:session['fastestLap']['lapNumber']=fastest['FastestLapNumLap']
    if race:session['raceDetails']={'raceType':info['raceType'],'isMajorRace':not sprint}
    elif phase:session['qualificationDetails']={'qualificationType':phase}
    season={'seasonName':f'F1 {year}','championshipName':f'F1 {year}','isMulticlass':False}
    if calendar:
        season['totalRounds']=len(calendar)
        season['completedRounds']=sum(e['date'][:10]<event_date or (e['date'][:10]==event_date and race and not sprint) for e in calendar)
    context={'round':round_no,'championshipPosition':round_no,'eventDate':event_date,'track':{'trackName':circuit['CircuitName'],'country':circuit['Nation'],'turnsCount':circuit['NumberTurns']}}
    if payload.get('event_date_time'):context['eventDateTime']=payload['event_date_time']
    elif race and not sprint:context['eventDateTime']=normalized['Date']
    if 'has_sprint' in payload:context.update(racesCount=2 if payload['has_sprint'] else 1,qualificationsCount=2 if payload['has_sprint'] else 1)
    return {'metadata':{'formatVersion':1,'exportType':'Session','exportedAt':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'sourceApplication':'Racing League Tools','leagueName':payload.get('league_name','Formula 1')},'season':season,'event':context,'session':session}