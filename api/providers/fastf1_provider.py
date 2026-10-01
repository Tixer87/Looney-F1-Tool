import os
from pathlib import Path
from typing import Any,Dict,List,Optional
from .base import SessionType
def _check_service_outage():
    import requests
    from .base import ProviderUnavailable
    try:response=requests.get("https://livetiming.formula1.com/static/Index.json",timeout=8)
    except (requests.ConnectionError,requests.Timeout) as exc:
        raise ProviderUnavailable(f"F1 timing service unreachable: {exc}") from exc
    if response.status_code==429 or response.status_code>=500:
        raise ProviderUnavailable(f"F1 timing service returned HTTP {response.status_code}")
def _cache_dir()->Path:
    path=Path(os.getenv("LOCALAPPDATA",Path.home()/"AppData"/"Local"))/"LooneyF1Tool"/"fastf1_cache"
    path.mkdir(parents=True,exist_ok=True)
    return path
def _ff1_candidates(session:SessionType)->List[str]:
    if session=="Q":return ["Q"]
    if session=="R":return ["R"]
    if session=="P":return ["FP1"]
    if session=="SQ":return ["SQ","SS"]
    return [session]
def schedule(season:int)->List[Dict[str,Any]]:
    try:
        import fastf1
        fastf1.Cache.enable_cache(str(_cache_dir()))
        rows=[]
        for _,event in fastf1.get_event_schedule(season).iterrows():
            round_no=int(event.get("RoundNumber",0))
            if round_no<=0:continue
            event_format=str(event.get("EventFormat","") or "")
            rows.append({"round":round_no,"date":str(event.get("EventDate","")),"raceName":event.get("EventName",""),"Circuit":{"circuitName":f"{event.get('Location','')} ({event.get('Country','')})"},"EventFormat":event_format,"hasSprint":"sprint" in event_format.lower()})
        rows.sort(key=lambda row:row["round"])
        return rows
    except Exception:return []
def export_payload(season:int,round_no:int,session:SessionType)->Optional[Dict[str,Any]]:
    import fastf1
    import pandas as pd
    from utils.logging_setup import get_logger
    log=get_logger(__name__)
    def ms(value):
        return 0 if pd.isna(value) else int(round(value.total_seconds()*1000))
    def number(value):
        return 0 if pd.isna(value) else int(value)
    code={"P":"FP1","Q1":"Q","Q2":"Q","Q3":"Q","SS":"SQ"}.get(session,session)
    try:
        fastf1.Cache.enable_cache(str(_cache_dir()))
        event=fastf1.get_event(season,round_no)
        if code=="SQ" and "Sprint Shootout" in event.values:code="SS"
        loaded=fastf1.get_session(season,round_no,code)
        loaded.load(laps=True,telemetry=False,weather=True,messages=True)
        if loaded.results.empty:
            _check_service_outage()
            return None
        drivers=[]
        is_race=session in ("R","S","SR")
        leaders=loaded.results[loaded.results["Position"]==1]
        leader_ms=ms(leaders.iloc[0].get("Time",pd.NaT)) if is_race and not leaders.empty else 0
        for _,row in loaded.results.iterrows():
            no=str(row.get("DriverNumber",""))
            laps=loaded.laps[loaded.laps["DriverNumber"]==no]
            timed=laps.dropna(subset=["LapTime"])
            if "Deleted" in timed:timed=timed[timed["Deleted"]!=True]
            best=timed.loc[timed["LapTime"].idxmin()] if not timed.empty else None
            best_ms=ms(best["LapTime"]) if best is not None else 0
            position=number(row.get("Position",0))
            if position<=0:position=len(drivers)+1
            total_ms=ms(row.get("Time",pd.NaT)) if is_race else best_ms
            if is_race and position>1 and 0<total_ms<leader_ms:total_ms+=leader_ms
            entry={
                "DriverNumber":no,
                "Driver":{"givenName":row.get("FirstName",""),"familyName":row.get("LastName","")},
                "Team":{"Name":row.get("TeamName","")},
                "Position":position,
                "GridPosition":number(row.get("GridPosition",0)),
                "Status":str(row.get("Status","Ok")) if is_race else "Ok",
                "TimeInt":total_ms,
                "FastestLapTimeInt":best_ms,
                "FastestLapNumLap":number(best["LapNumber"]) if best is not None else 0,
                "LapsCount":number(row.get("Laps",len(laps))),
                "PitsCount":int(laps["PitInTime"].notna().sum())
            }
            if not pd.isna(row.get("Points",float("nan"))):entry["Points"]=str(row["Points"])
            if session in ("Q","Q1","Q2","Q3","SQ","SS"):
                for q in ("Q1","Q2","Q3"):entry[q]=ms(row.get(q,pd.NaT))
            drivers.append(entry)
        calendar=fastf1.get_event_schedule(season,include_testing=False)
        return {
            "season":season,
            "round":round_no,
            "session":session,
            "calendar":[{"round":int(e.RoundNumber),"date":str(e.EventDate.date()),"location":e.Location} for _,e in calendar.iterrows()],
            "has_sprint":"sprint" in str(event.EventFormat).lower(),
            "circuit":str(event.Location),
            "date":loaded.date.isoformat(),
            "Drivers":drivers,
            "source":"fastf1"
        }
    except Exception as exc:
        from .fallback import is_unreachable
        if is_unreachable(exc):raise
        _check_service_outage()
        log.warning("FastF1 %s %s %s unavailable: %s",season,round_no,session,exc)
        return None