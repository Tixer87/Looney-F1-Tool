# api/jolpica_api.py

import requests
import sys
import os
import time
from utils.rate_limit import enforce_rate_limit
from utils.config_loader import get_api_base_url
from utils.logging_setup import get_context_logger

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Initialize logger with provider context
log = get_context_logger(__name__, {"provider": "jolpica"})

# Use centralized config instead of hardcoded URL
def get_base_url():
    return get_api_base_url()

@enforce_rate_limit
def get_season_drivers(year):
    base_url = get_base_url()
    url = f"{base_url}/{year}/drivers.json"
    
    start = time.perf_counter()
    log.debug("Fetching season drivers", year=year, url=url)
    
    response = requests.get(url, timeout=30)
    duration_ms = int((time.perf_counter() - start) * 1000)
    
    if response.status_code == 200:
        drivers = response.json()["MRData"]["DriverTable"]["Drivers"]
        log.info("Fetched season drivers", year=year, count=len(drivers), 
                duration_ms=duration_ms, http_status=response.status_code)
        return drivers
    else:
        log.error("API error fetching drivers", year=year, http_status=response.status_code,
                 duration_ms=duration_ms)
        return []

@enforce_rate_limit
def fetch_race_data(year, round_number=None, endpoint="results"):
    base_url = get_base_url()
    import requests
    if round_number is not None:
        url = f"{base_url}/{year}/{round_number}/{endpoint}.json"
    else:
        url = f"{base_url}/{year}/{endpoint}.json"
    
    start = time.perf_counter()
    log.debug("Fetching race data", year=year, round=round_number, endpoint=endpoint)
    
    response = requests.get(url, timeout=30)
    duration_ms = int((time.perf_counter() - start) * 1000)
    
    if response.status_code == 200:
        log.info("Fetched race data", year=year, round=round_number, endpoint=endpoint,
                duration_ms=duration_ms, http_status=response.status_code)
        return response.json()
    else:
        log.error("API error fetching race data", year=year, round=round_number, 
                 endpoint=endpoint, http_status=response.status_code, duration_ms=duration_ms)
        return {}
@enforce_rate_limit
def fetch_pitstops_data(year, round_number):
    """
    Holt die Pitstop-Daten eines Rennens aus der Jolpica-API.
    Gibt eine Liste aller Stopps zurück.
    """
    base_url = get_base_url()
    url = f"{base_url}/{year}/{round_number}/pitstops.json"
    
    start = time.perf_counter()
    log.debug("Fetching pitstops", year=year, round=round_number)
    
    response = requests.get(url, timeout=30)
    duration_ms = int((time.perf_counter() - start) * 1000)
    
    if response.status_code == 200:
        races = response.json().get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if races and "PitStops" in races[0]:
            pitstops = races[0]["PitStops"]
            log.info("Fetched pitstops", year=year, round=round_number, count=len(pitstops),
                    duration_ms=duration_ms, http_status=response.status_code)
            return pitstops
        else:
            log.warning("No pitstop data found", year=year, round=round_number,
                       duration_ms=duration_ms, http_status=response.status_code)
            return []
    else:
        log.error("API error fetching pitstops", year=year, round=round_number,
                 http_status=response.status_code, duration_ms=duration_ms)
        return []
@enforce_rate_limit
def fetch_sprint_data(year):
    base_url = get_base_url()
    url = f"{base_url}/{year}/sprint.json"
    
    start = time.perf_counter()
    log.debug("Fetching sprint data", year=year)
    
    response = requests.get(url, timeout=30)
    duration_ms = int((time.perf_counter() - start) * 1000)
    
    if response.status_code == 200:
        log.info("Fetched sprint data", year=year, duration_ms=duration_ms, 
                http_status=response.status_code)
        return response.json()
    else:
        log.error("API error fetching sprint data", year=year, 
                 http_status=response.status_code, duration_ms=duration_ms)
        return {}
