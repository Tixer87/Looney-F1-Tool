import time
import requests
from api.providers.base import ProviderUnavailable
from utils.rate_limit import enforce_rate_limit
from utils.config_loader import get_api_base_url
from utils.logging_setup import get_context_logger
log=get_context_logger(__name__,{"provider":"jolpica"})
DEFAULT_TIMEOUT=8
class JolpicaError(RuntimeError):pass
def get_base_url():
    return get_api_base_url()
def _duration(start):
    return int((time.perf_counter()-start)*1000)
def _get(url:str,*,timeout:int=DEFAULT_TIMEOUT)->dict:
    response=requests.get(url,timeout=timeout)
    if response.status_code==200:
        try:return response.json()
        except ValueError as exc:raise JolpicaError(f"Invalid JSON from {url}") from exc
    if response.status_code in (429,502,503,504) or response.status_code>=500:
        raise ProviderUnavailable(f"Server status {response.status_code} for {url}")
    raise JolpicaError(f"HTTP {response.status_code} for {url}")
def healthcheck(max_retries:int=3,base_delay:float=1.25)->bool:
    url=f"{get_base_url()}/seasons.json?limit=1"
    for i in range(max_retries):
        try:return "MRData" in _get(url)
        except (JolpicaError,ProviderUnavailable,requests.RequestException):
            time.sleep(base_delay*(i+1))
    return False
def fetch_drivers(year:int)->dict:
    return _get(f"{get_base_url()}/{year}/drivers.json?limit=1000")
def fetch_results(year:int,round_no:int,session:str)->dict:
    session=session.lower()
    if session in ("race","main","r"):endpoint="results"
    elif session in ("qualifying","qualification","quali","q"):endpoint="qualifying"
    elif session in ("s","sr","sprint"):endpoint="sprint"
    else:raise ValueError(f"Jolpica does not provide session {session!r}")
    return _get(f"{get_base_url()}/{year}/{round_no}/{endpoint}.json?limit=1000")
def fetch_schedule(year:int)->dict:
    return _get(f"{get_base_url()}/{year}.json?limit=100")
@enforce_rate_limit
def get_season_drivers(year):
    url=f"{get_base_url()}/{year}/drivers.json"
    start=time.perf_counter()
    log.debug("Fetching season drivers",year=year,url=url)
    response=requests.get(url,timeout=30)
    duration=_duration(start)
    if response.status_code==200:
        drivers=response.json()["MRData"]["DriverTable"]["Drivers"]
        log.info("Fetched season drivers",year=year,count=len(drivers),duration_ms=duration,http_status=response.status_code)
        return drivers
    log.error("API error fetching drivers",year=year,http_status=response.status_code,duration_ms=duration)
    return []
@enforce_rate_limit
def fetch_race_data(year,round_number=None,endpoint="results"):
    url=f"{get_base_url()}/{year}/{round_number}/{endpoint}.json" if round_number is not None else f"{get_base_url()}/{year}/{endpoint}.json"
    start=time.perf_counter()
    log.debug("Fetching race data",year=year,round=round_number,endpoint=endpoint)
    response=requests.get(url,timeout=30)
    duration=_duration(start)
    if response.status_code==200:
        log.info("Fetched race data",year=year,round=round_number,endpoint=endpoint,duration_ms=duration,http_status=response.status_code)
        return response.json()
    log.error("API error fetching race data",year=year,round=round_number,endpoint=endpoint,http_status=response.status_code,duration_ms=duration)
    return {}
@enforce_rate_limit
def fetch_pitstops_data(year,round_number):
    url=f"{get_base_url()}/{year}/{round_number}/pitstops.json"
    start=time.perf_counter()
    log.debug("Fetching pitstops",year=year,round=round_number)
    response=requests.get(url,timeout=30)
    duration=_duration(start)
    if response.status_code!=200:
        log.error("API error fetching pitstops",year=year,round=round_number,http_status=response.status_code,duration_ms=duration)
        return []
    races=response.json().get("MRData",{}).get("RaceTable",{}).get("Races",[])
    if races and "PitStops" in races[0]:
        pitstops=races[0]["PitStops"]
        log.info("Fetched pitstops",year=year,round=round_number,count=len(pitstops),duration_ms=duration,http_status=response.status_code)
        return pitstops
    log.warning("No pitstop data found",year=year,round=round_number,duration_ms=duration,http_status=response.status_code)
    return []
@enforce_rate_limit
def fetch_sprint_data(year):
    url=f"{get_base_url()}/{year}/sprint.json"
    start=time.perf_counter()
    log.debug("Fetching sprint data",year=year)
    response=requests.get(url,timeout=30)
    duration=_duration(start)
    if response.status_code==200:
        log.info("Fetched sprint data",year=year,duration_ms=duration,http_status=response.status_code)
        return response.json()
    log.error("API error fetching sprint data",year=year,http_status=response.status_code,duration_ms=duration)
    return {}