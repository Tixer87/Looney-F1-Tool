# api/providers/jolpica_api.py
from __future__ import annotations
import time
import requests

BASE = "http://api.jolpi.ca/ergast/f1"
DEFAULT_TIMEOUT = 8

class JolpicaError(RuntimeError):
    pass

def _get(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> dict:
    r = requests.get(url, timeout=timeout)
    if r.status_code == 200:
        try:
            return r.json()
        except ValueError as e:
            raise JolpicaError(f"Invalid JSON from {url}") from e
    if r.status_code in (429, 502, 503, 504):
        raise JolpicaError(f"Transient status {r.status_code} for {url}")
    raise JolpicaError(f"HTTP {r.status_code} for {url}")

def healthcheck(max_retries: int = 3, base_delay: float = 1.25) -> bool:
    url = f"{BASE}/seasons.json?limit=1"
    for i in range(max_retries):
        try:
            data = _get(url)
            return "MRData" in data
        except JolpicaError:
            time.sleep(base_delay * (i + 1))
        except requests.RequestException:
            time.sleep(base_delay * (i + 1))
    return False

def fetch_drivers(year: int) -> dict:
    url = f"{BASE}/{year}/drivers.json?limit=1000"
    return _get(url)

def fetch_results(year: int, round_no: int, session: str) -> dict:
    # Ergast-stil kennt keine „session"-Pfadsegmente; wir holen Race/Quali über results/qualifying
    if session.lower() in ("race", "main", "r"):
        url = f"{BASE}/{year}/{round_no}/results.json?limit=1000"
    elif session.lower() in ("qualifying", "qualification", "quali", "q"):
        url = f"{BASE}/{year}/{round_no}/qualifying.json?limit=1000"
    else:
        # Fallback: letzte Ergebnisse
        url = f"{BASE}/current/last/results.json"
    return _get(url)

def fetch_schedule(year: int) -> dict:
    url = f"{BASE}/{year}.json?limit=100"
    return _get(url)
