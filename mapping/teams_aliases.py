import json
from pathlib import Path
from typing import Optional
from mapping.normalize import normalize_key
from utils.logging_setup import get_logger
log=get_logger(__name__)
ALIAS_FILE=Path(__file__).parent/"team_alias_map.json"
_alias_map={}
_loaded=False
def _load_data():
    global _alias_map,_loaded
    if _loaded:return
    try:
        with open(ALIAS_FILE,"r",encoding="utf-8") as f:raw=json.load(f)
        _alias_map={normalize_key(key):value for key,value in raw.items()}
        log.info("Team aliases loaded: %s mappings",len(_alias_map))
    except FileNotFoundError:
        log.error("team_alias_map.json not found: %s",ALIAS_FILE)
        _alias_map={}
    _loaded=True
_load_data()
def _result(info,year):
    prefix=info["UniquePrefix"]
    unique=prefix.rstrip(".") if year is None else f"{prefix}{year}"
    return {"Name":info["Name"],"UniqueName":unique,"Abbr":info["Abbr"]}
def get_team_name(raw:object,year:Optional[int]=None)->dict:
    if not raw:
        log.warning("Empty team input")
        return {"Name":"Unknown Team","UniqueName":"Unknown","Abbr":"UNK"}
    constructor_id=None
    name=None
    if isinstance(raw,dict):
        constructor_id=raw.get("constructorId")
        name=raw.get("Name") or raw.get("name")
    elif isinstance(raw,str):name=raw
    else:
        log.warning("Unsupported team input type: %s",type(raw).__name__)
        return {"Name":"Unknown Team","UniqueName":"Unknown","Abbr":"UNK"}
    if constructor_id:
        info=_alias_map.get(normalize_key(f"constructor:{constructor_id}"))
        if info:return _result(info,year)
    if name:
        info=_alias_map.get(normalize_key(name))
        if info:return _result(info,year)
        if len(name.strip())>2:
            log.warning("Team not in alias map: %s",name)
            return {"Name":name.strip(),"UniqueName":normalize_key(name),"Abbr":"UNK"}
    log.warning("Team lookup failed for: %s",raw)
    return {"Name":"Unknown Team","UniqueName":"Unknown","Abbr":"UNK"}
def list_all_teams(year:Optional[int]=None)->list[dict]:
    teams={}
    for info in _alias_map.values():
        key=info.get("UniquePrefix",info.get("Name",""))
        if key and key not in teams:teams[key]=_result(info,year)
    return list(teams.values())