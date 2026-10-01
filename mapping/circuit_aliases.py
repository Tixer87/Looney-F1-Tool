"""Strict circuit resolution without external RLT mapping files."""
from typing import Tuple
from mapping.normalize import normalize_key
from utils.logging_setup import get_logger
log=get_logger(__name__)
CIRCUITS=[
{"UniqueName":"austin.2012","CircuitName":"Austin","LocationName":"Austin","Nation":"United States Of America","NumberTurns":20,"Aliases":["Circuit of the Americas","COTA","Austin","United States Grand Prix"]},
{"UniqueName":"sakhir.2005","CircuitName":"Bahrain","LocationName":"Sakhir","Nation":"Bahrain","NumberTurns":15,"Aliases":["Bahrain International Circuit","Sakhir","Bahrain","Bahrain Grand Prix"]},
{"UniqueName":"baku.2016","CircuitName":"Baku","LocationName":"Baku","Nation":"Azerbaijan","NumberTurns":20,"Aliases":["Baku City Circuit","Baku","Azerbaijan Grand Prix"]},
{"UniqueName":"barcelona.2021","CircuitName":"Barcelona","LocationName":"Montmeló","Nation":"Spain","NumberTurns":14,"Aliases":["Circuit de Barcelona-Catalunya","Barcelona","Spanish Grand Prix"]},
{"UniqueName":"hungaroring.2003","CircuitName":"Hungaroring","LocationName":"Mogyoród","Nation":"Hungary","NumberTurns":14,"Aliases":["Hungaroring","Budapest","Hungarian Grand Prix"]},
{"UniqueName":"imola.2008","CircuitName":"Imola","LocationName":"Imola","Nation":"Italy","NumberTurns":19,"Aliases":["Imola","Autodromo Enzo e Dino Ferrari","Autodromo Internazionale Enzo e Dino Ferrari","Emilia Romagna Grand Prix"]},
{"UniqueName":"interlagos.2000","CircuitName":"Interlagos","LocationName":"São Paulo","Nation":"Brazil","NumberTurns":15,"Aliases":["Interlagos","Autódromo José Carlos Pace","Sao Paulo","São Paulo","São Paulo Grand Prix","Brazilian Grand Prix"]},
{"UniqueName":"jeddah.2021","CircuitName":"Jeddah","LocationName":"Jeddah","Nation":"Saudi Arabia","NumberTurns":27,"Aliases":["Jeddah Corniche Circuit","Jeddah","Saudi Arabian Grand Prix"]},
{"UniqueName":"albert.park.2021","CircuitName":"Melbourne","LocationName":"Melbourne","Nation":"Australia","NumberTurns":14,"Aliases":["Albert Park Circuit","Melbourne","Albert Park Grand Prix Circuit","Australian Grand Prix"]},
{"UniqueName":"mexico.2015","CircuitName":"Mexico","LocationName":"Mexico City","Nation":"Mexico","NumberTurns":17,"Aliases":["Autódromo Hermanos Rodríguez","Mexico City Grand Prix","Mexico","Mexico City","Mexican Grand Prix"]},
{"UniqueName":"monaco.2015","CircuitName":"Monaco","LocationName":"Monaco","Nation":"Monaco","NumberTurns":19,"Aliases":["Circuit de Monaco","Monaco","Monaco Grand Prix","Monte Carlo"]},
{"UniqueName":"montreal.2002","CircuitName":"Montreal","LocationName":"Montreal","Nation":"Canada","NumberTurns":14,"Aliases":["Circuit Gilles Villeneuve","Montreal","Montréal","Canadian Grand Prix"]},
{"UniqueName":"monza.2000","CircuitName":"Monza","LocationName":"Monza","Nation":"Italy","NumberTurns":11,"Aliases":["Autodromo Nazionale di Monza","Monza","Italian Grand Prix"]},
{"UniqueName":"shanghai.2004","CircuitName":"Shanghai","LocationName":"Shanghai","Nation":"China","NumberTurns":16,"Aliases":["Shanghai International Circuit","Shanghai","Chinese Grand Prix"]},
{"UniqueName":"silverstone.2011","CircuitName":"Silverstone","LocationName":"Silverstone","Nation":"United Kingdom","NumberTurns":18,"Aliases":["Silverstone Circuit","Silverstone","British Grand Prix"]},
{"UniqueName":"singapore.2018","CircuitName":"Singapore","LocationName":"Downtown Core","Nation":"Singapore","NumberTurns":23,"Aliases":["Marina Bay Street Circuit","Singapore","Marina Bay"]},
{"UniqueName":"singapore.2023","CircuitName":"Singapore","LocationName":"Downtown Core","Nation":"Singapore","NumberTurns":19,"Aliases":["Marina Bay Street Circuit","Singapore","Marina Bay","Singapore Grand Prix"]},
{"UniqueName":"spa.2007","CircuitName":"Spa-Francorchamps","LocationName":"Stavelot","Nation":"Belgium","NumberTurns":20,"Aliases":["Spa","Spa-Francorchamps","Circuit de Spa-Francorchamps","Belgian Grand Prix"]},
{"UniqueName":"spielberg.2016","CircuitName":"Spielberg","LocationName":"Spielberg","Nation":"Austria","NumberTurns":10,"Aliases":["Red Bull Ring","Spielberg","Austrian Grand Prix"]},
{"UniqueName":"suzuka.2003","CircuitName":"Suzuka","LocationName":"Suzuka","Nation":"Japan","NumberTurns":18,"Aliases":["Suzuka Circuit","Suzuka International Circuit","Suzuka International Racing Course","Suzuka","Japanese Grand Prix"]},
{"UniqueName":"yasmarina.2021","CircuitName":"Yas Marina","LocationName":"Yas Island","Nation":"United Arab Emirates","NumberTurns":16,"Aliases":["Yas Marina Circuit","Yas Marina","Yas Island","Abu Dhabi Grand Prix"]},
{"UniqueName":"zandvoort.2020","CircuitName":"Zandvoort","LocationName":"Zandvoort","Nation":"Netherlands","NumberTurns":14,"Aliases":["Circuit Zandvoort","Zandvoort","Dutch Grand Prix"]},
{"UniqueName":"miami.2022","CircuitName":"Miami","LocationName":"Miami Gardens","Nation":"United States Of America","NumberTurns":19,"Aliases":["Miami International Autodrome","Miami","Miami Gardens","Miami Grand Prix"]},
{"UniqueName":"losail.2023","CircuitName":"Losail","LocationName":"Lusail","Nation":"Qatar","NumberTurns":16,"Aliases":["Losail International Circuit","Losail","Lusail","Qatar Grand Prix"]},
{"UniqueName":"las.vegas.2023","CircuitName":"Las Vegas","LocationName":"Las Vegas","Nation":"United States Of America","NumberTurns":17,"Aliases":["Las Vegas Strip Circuit","Las Vegas","Las Vegas Grand Prix"]},
{"UniqueName":"sepang.1999","CircuitName":"Sepang","LocationName":"Sepang","Nation":"Malaysia","NumberTurns":15,"Aliases":["Kuala Lumpur","Sepang","Sepang International Circuit"]},
{"UniqueName":"madrid.2026","CircuitName":"Madrid","LocationName":"Madrid","Nation":"Spain","NumberTurns":22,"Aliases":["Madrid","Madring","Madring Street Circuit"]}
]
_BY_UNIQUE={}
_BY_NAME={}
for circuit in CIRCUITS:
    _BY_UNIQUE[normalize_key(circuit["UniqueName"])]=circuit
    for value in [circuit["CircuitName"],circuit["LocationName"],*circuit["Aliases"]]:
        key=normalize_key(value)
        if key:_BY_NAME[key]=circuit
log.info("Circuits loaded: %s total, %s aliases",len(CIRCUITS),len(_BY_NAME))
def _resolve(value):
    key=normalize_key(value)
    return _BY_UNIQUE.get(key) or _BY_NAME.get(key)
def get_circuit(raw:object)->Tuple[str,str]:
    if not raw:raise ValueError("Empty circuit input - cannot proceed with STRICT matching")
    if isinstance(raw,dict):
        for key in ("circuitId","jolpicaCircuitId","CircuitName","circuitName","name","UniqueName"):
            if raw.get(key):
                circuit=_resolve(raw[key])
                if circuit:return circuit["CircuitName"],circuit["UniqueName"]
        raise ValueError(f"Circuit dict has no matching entry: {raw}")
    if isinstance(raw,str):
        circuit=_resolve(raw)
        if circuit:return circuit["CircuitName"],circuit["UniqueName"]
        raise ValueError(f"Circuit string not found (STRICT mode): '{raw}'")
    raise ValueError(f"Unsupported circuit input type: {type(raw).__name__}")
def get_circuit_info(raw):
    _,unique=get_circuit(raw)
    return _BY_UNIQUE[normalize_key(unique)].copy()
def get_circuit_by_unique(unique_name):
    circuit=_BY_UNIQUE.get(normalize_key(unique_name))
    return circuit.copy() if circuit else None
def list_available_circuits():
    return [{"CircuitName":c["CircuitName"],"UniqueName":c["UniqueName"]} for c in CIRCUITS]