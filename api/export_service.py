from __future__ import annotations
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any,Dict,Literal,Optional
from utils.logging_setup import get_logger
try:
    from api.providers.router import get_provider
except ImportError:
    from .providers.router import get_provider
log=get_logger(__name__)
SESSION_GROUPS={"Practice":["FP1","FP2","FP3"],"Qualifying":["Q"],"Sprint":["SQ","S"],"Race":["R"],"All Sessions":["FP1","FP2","FP3","SQ","S","Q","R"]}
SessionType=Literal["FP1","FP2","FP3","Q1","Q2","Q3","P","Q","SQ","SS","S","R"]
def expand_session_group(session_input:str)->list[str]:
    return SESSION_GROUPS.get(session_input,[session_input])
def resource_path(rel:str)->Path:
    base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent.parent))
    return (base/rel).resolve()
def load_json(rel:str):
    with open(resource_path(rel),"r",encoding="utf-8") as f:return json.load(f)
def safe_name(value:str)->str:
    return re.sub(r"\s+","_",re.sub(r"[^\w\s\-.]","",value.strip()))
def build_output_name(season:int,round_no:int,session:str,quali_phase:Optional[str],event:Dict[str,Any])->str:
    if "Circuit" in event:circuit=event["Circuit"].get("circuitName","")
    elif "circuitName" in event:circuit=event["circuitName"]
    elif "raceName" in event:circuit=event["raceName"]
    else:circuit=""
    circuit=safe_name(circuit or f"Round_{round_no}")
    if session in {"Q1","Q2","Q3"}:return f"{season}_{circuit}_{session}.json"
    if session=="Q" and quali_phase:return f"{season}_{circuit}_Qualifying_{quali_phase}.json"
    if session=="Q":return f"{season}_{circuit}_Qualifying.json"
    if session in {"FP1","FP2","FP3"}:return f"{season}_{circuit}_{session}.json"
    if session=="P":return f"{season}_{circuit}_Practice.json"
    if session=="SQ":return f"{season}_{circuit}_Sprint_Qualifying.json"
    if session=="SS":return f"{season}_{circuit}_Sprint_Shootout.json"
    if session in {"S","SR"}:return f"{season}_{circuit}_Sprint_Race.json"
    if session=="R":return f"{season}_{circuit}_Race.json"
    return f"{season}_{circuit}_{session}.json"
def unique_path(directory:Path,filename:str)->Path:
    path=directory/filename
    if not path.exists():return path
    counter=2
    while True:
        candidate=directory/f"{path.stem}_{counter:02d}{path.suffix}"
        if not candidate.exists():return candidate
        counter+=1
def _infer_session_type(session:str)->str:
    if session in {"Q","Q1","Q2","Q3","SQ","SS"}:return "Qualification"
    if session in {"P","FP1","FP2","FP3"}:return "Practice"
    return "Race"
def session_allowed_by_schedule(season:int,round_no:int,session:str)->bool:
    if session!="SQ":return True
    try:
        event=next((x for x in get_provider(year=season).schedule(season) if int(x.get("round",0))==round_no),None)
        return bool(event and event.get("hasSprint",False))
    except Exception:
        return True
def _find_event(season:int,round_no:int)->Dict[str,Any]:
    try:return next((x for x in get_provider(year=season).schedule(season) if int(x.get("round",0))==round_no),{})
    except Exception:return {}
def run_export(season:int,round_no:int,session:SessionType,out_dir:Path,verbose:bool=False)->Optional[Path]:
    valid={"FP1","FP2","FP3","P","Q","Q1","Q2","Q3","SQ","SS","S","R"}
    if session not in valid:raise ValueError(f"Invalid session type: {session}")
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    from api.providers.fallback import fetch_with_fallback
    payload=fetch_with_fallback(get_provider(year=season),season,round_no,session)
    if not payload or not payload.get("Drivers"):return None
    event={"circuitName":payload.get("circuit") or f"Round_{round_no}"}
    payload.update(season=season,session_type=_infer_session_type(session),race_type="Sprint" if session in {"SQ","SS","S"} else "Regular")
    phases=["Q1","Q2","Q3"] if session in {"Q","SQ","SS"} else [session]
    results=[]
    from export.native_rlt import build_native_session
    for phase in phases:
        data=copy.deepcopy(payload)
        if phase in {"Q1","Q2","Q3"}:data.update(qual_type=phase,_current_q_session=phase)
        result=build_native_session(data)
        if not result["session"]["drivers"]:continue
        validate_export(result)
        code="S"+phase if session in {"SQ","SS"} else phase
        target=unique_path(out_dir,build_output_name(season,round_no,code,None,event))
        target.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
        results.append(target)
        if verbose:print(f"Exported {code}: {target}")
    return results[-1] if results else None
def validate_export(result:dict)->None:
    from jsonschema import Draft202012Validator,FormatChecker
    schema=load_json("export/native_session.schema.json" if "metadata" in result else "export/rlt_session.schema.json")
    Draft202012Validator(schema,format_checker=FormatChecker()).validate(result)