import json
import threading
import time
from datetime import datetime,timedelta
from pathlib import Path
import requests
from .base import ProviderDataError,ProviderUnavailable
_lock=threading.Lock()
_last_request=0.0
def _get(endpoint,*,allow_missing=False,**params):
    global _last_request
    with _lock:
        time.sleep(max(0,2.1-(time.monotonic()-_last_request)))
        _last_request=time.monotonic()
        try:
            response=requests.get("https://api.openf1.org/v1/"+endpoint,params=params,timeout=20)
            if allow_missing and response.status_code==404:return []
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderUnavailable(f"OpenF1 request failed: {exc}") from exc
        data=response.json()
    if not isinstance(data,list):raise ProviderDataError("OpenF1 returned an unexpected response")
    return data
class OpenF1Provider:
    name="openf1"
    def fetch_session_raw(self,year,round_no,session_type):
        from mapping.circuit_aliases import get_circuit
        path=Path(__file__).resolve().parents[2]/"mapping"/"fallback_calendars.json"
        calendars=json.loads(path.read_text(encoding="utf-8"))
        event=next((e for e in calendars.get(str(year),[]) if e["round"]==round_no),None)
        if not event:raise ProviderDataError(f"No verified OpenF1 round mapping for {year} R{round_no}")
        names={"FP1":"Practice 1","P":"Practice 1","FP2":"Practice 2","FP3":"Practice 3","Q":"Qualifying","Q1":"Qualifying","Q2":"Qualifying","Q3":"Qualifying","R":"Race","S":"Sprint","SQ":"Sprint Qualifying","SS":"Sprint Qualifying"}
        sessions=_get("sessions",year=year,session_name=names[session_type])
        race_date=datetime.fromisoformat(event["date"]).date()
        candidates=[]
        for session in sessions:
            date=datetime.fromisoformat(session["date_start"]).date()
            if not race_date-timedelta(days=4)<=date<=race_date+timedelta(days=1):continue
            try:track=get_circuit(session["circuit_short_name"])[1]
            except ValueError:continue
            if track==get_circuit(event["location"])[1] and not session.get("is_cancelled"):candidates.append(session)
        if not candidates:return {"Drivers":[]}
        if len(candidates)!=1:raise ProviderDataError("Ambiguous OpenF1 session; refusing to guess")
        selected=candidates[0]
        key=selected["session_key"]
        results=_get("session_result",session_key=key)
        if not results:return {"Drivers":[]}
        people={r["driver_number"]:r for r in _get("drivers",session_key=key)}
        race=session_type in ("R","S")
        grid={r["driver_number"]:r["position"] for r in _get("starting_grid",allow_missing=True,session_key=key)} if race else {}
        if race and not grid:
            from utils.logging_setup import get_logger
            get_logger(__name__).warning("OpenF1 has no starting grid; unknown grid positions remain 0")
        drivers=[]
        next_unclassified=max((r.get("position") or 0 for r in results),default=0)
        def ms(value):
            return int(round(float(value)*1000)) if value is not None else 0
        for row in results:
            no=row["driver_number"]
            person=people.get(no)
            if not person:raise ProviderDataError(f"OpenF1 driver metadata missing: {no}")
            duration=row.get("duration")
            q=duration if isinstance(duration,list) else None
            position=row.get("position")
            if not position:
                if not any(row.get(flag) for flag in ("dnf","dns","dsq")):raise ProviderDataError(f"OpenF1 classification missing for driver {no}")
                next_unclassified+=1
                position=next_unclassified
            entry={
                "Driver":{"givenName":person["first_name"],"familyName":person["last_name"]},
                "RaceNumber":no,
                "Team":{"Name":person["team_name"]},
                "Position":position,
                "GridPosition":grid.get(no,0),
                "Status":"Disqualified" if row.get("dsq") else "Did not start" if row.get("dns") else "Retired" if row.get("dnf") else "Finished",
                "TimeInt":0 if q else ms(duration),
                "FastestLapTimeInt":0 if race or q else ms(duration),
                "LapsCount":row.get("number_of_laps") or 0,
                "PitsCount":0
            }
            if q:
                for index,phase in enumerate(("Q1","Q2","Q3")):entry[phase]=ms(q[index]) if index<len(q) else 0
            if row.get("points") is not None:entry["Points"]=str(row["points"])
            drivers.append(entry)
        return {"source":self.name,"season":year,"round":round_no,"circuit":event["location"],"date":selected["date_start"],"Drivers":drivers}