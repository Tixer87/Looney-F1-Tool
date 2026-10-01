import json
from pathlib import Path
from typing import Optional
from mapping.normalize import normalize_key
from utils.logging_setup import get_logger
log=get_logger(__name__)
ALIAS_FILE=Path(__file__).parent/"driver_alias_map.json"
_drivers={}
_aliases={}
_loaded=False
def _display_name(value:str)->str:
    return " ".join(part.capitalize() for part in value.split())
def _load_data():
    global _drivers,_aliases,_loaded
    if _loaded:return
    try:
        with open(ALIAS_FILE,"r",encoding="utf-8") as f:raw=json.load(f)
        for alias,variations in raw.items():
            if not variations:continue
            canonical=normalize_key(variations[0])
            if canonical not in _drivers:
                _drivers[canonical]={"Name":_display_name(variations[0]),"SeatType":"Primary"}
            _aliases[normalize_key(alias)]=canonical
            _aliases[canonical]=canonical
            for variation in variations:_aliases[normalize_key(variation)]=canonical
        log.info("Driver aliases loaded: %s drivers, %s names",len(_drivers),len(_aliases))
    except FileNotFoundError:
        log.error("driver_alias_map.json not found: %s",ALIAS_FILE)
        _drivers={}
        _aliases={}
    _loaded=True
_load_data()
def get_driver_by_number(number:int,year:int=2025)->Optional[dict]:
    return None
def get_driver_by_code(code:str,year:int=2025)->Optional[dict]:
    return get_driver_by_name(code,year)
def get_driver_by_name(name:str,year:int=2025)->Optional[dict]:
    if not name:return None
    canonical=_aliases.get(normalize_key(name))
    if canonical:return _drivers[canonical].copy()
    log.warning("Driver not found by name: %s",name)
    return None
def get_driver(raw:object,year:int=2025)->Optional[dict]:
    if isinstance(raw,str):return get_driver_by_name(raw,year)
    if isinstance(raw,dict):
        name=raw.get("name") or raw.get("Name") or raw.get("fullName")
        if name:return get_driver_by_name(name,year)
    log.warning("Driver lookup failed for: %s",raw)
    return None
def list_all_drivers(year:int=2025)->list[dict]:
    return [driver.copy() for driver in _drivers.values()]
def get_driver_full_info(name:str,year:int=2025)->Optional[dict]:
    return get_driver_by_name(name,year)