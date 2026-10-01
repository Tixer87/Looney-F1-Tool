import json
from pathlib import Path
from mapping.normalize import normalize_key
from utils.logging_setup import get_logger
log=get_logger(__name__)
ALIAS_FILE=Path(__file__).parent/"nations_alias_map.json"
NATIONS={
"Argentina":"ARG","Australia":"AUS","Austria":"AUT","Azerbaijan":"AZE","Bahrain":"BHR","Belgium":"BEL","Brazil":"BRA","Canada":"CAN","China":"CHN","Denmark":"DEN","Finland":"FIN","France":"FRA","Germany":"GER","Hungary":"HUN","Italy":"ITA","Japan":"JPN","Mexico":"MEX","Monaco":"MON","Netherlands":"NLD","New Zealand":"NZL","Poland":"POL","Russia":"RUS","Saudi Arabia":"KSA","Spain":"ESP","Switzerland":"SUI","Thailand":"THA","United Arab Emirates":"UAE","United Kingdom":"GBR","United States":"USA","United States Of America":"USA","Venezuela":"VEN"
}
_BY_NAME={normalize_key(name):(name,code) for name,code in NATIONS.items()}
_BY_CODE={normalize_key(code):(name,code) for name,code in NATIONS.items()}
_alias_map={}
_loaded=False
def _load_data():
    global _alias_map,_loaded
    if _loaded:return
    try:
        with open(ALIAS_FILE,"r",encoding="utf-8") as f:raw=json.load(f)
        _alias_map={normalize_key(alias):canonical for alias,canonical in raw.items()}
        log.info("Nation aliases loaded: %s mappings",len(_alias_map))
    except FileNotFoundError:
        log.warning("nations_alias_map.json not found: %s",ALIAS_FILE)
        _alias_map={}
    _loaded=True
_load_data()
def get_driver_nation(raw:str)->dict:
    if not raw or not isinstance(raw,str):
        log.warning("Invalid nationality input: %s",raw)
        return {"Name":"Unknown","Code":"UNK"}
    normalized=normalize_key(raw)
    canonical=_alias_map.get(normalized)
    if canonical:
        match=_BY_NAME.get(normalize_key(canonical))
        if match:return {"Name":match[0],"Code":match[1]}
    match=_BY_NAME.get(normalized)
    if match:return {"Name":match[0],"Code":match[1]}
    match=_BY_CODE.get(normalized)
    if match:return {"Name":match[0],"Code":match[1]}
    log.warning("Nationality not mapped: %s",raw)
    return {"Name":canonical or raw.strip(),"Code":"UNK"}
def list_all_nations()->list[dict]:
    return [{"Name":name,"Code":code} for name,code in NATIONS.items()]