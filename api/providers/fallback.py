import requests
from .base import ProviderUnavailable
from .jolpica_provider import JolpicaProvider
from .openf1_provider import OpenF1Provider
from .router import FastF1ProviderWrapper
from utils.logging_setup import get_logger
log=get_logger(__name__)
def is_unreachable(exc):
    if isinstance(exc,(ProviderUnavailable,requests.ConnectionError,requests.Timeout)):return True
    return isinstance(exc,requests.HTTPError) and exc.response is not None and (exc.response.status_code==429 or exc.response.status_code>=500)
def fetch_with_fallback(primary,year,round_no,session):
    providers=[primary]
    if primary.name!="fastf1":providers.append(FastF1ProviderWrapper())
    if primary.name!="jolpica" and session in {"R","S","Q","Q1","Q2","Q3"}:providers.append(JolpicaProvider())
    failures=[]
    for provider in providers:
        try:payload=provider.fetch_session_raw(year,round_no,session)
        except Exception as exc:
            if not is_unreachable(exc):raise
            failures.append(exc)
            log.warning("%s unreachable: %s",provider.name,exc)
            continue
        if payload and payload.get("Drivers"):return payload
    if len(failures)==len(providers):
        if year<2023:raise ProviderUnavailable("All providers unreachable; OpenF1 starts in 2023") from failures[-1]
        log.warning("All applicable existing providers unreachable; using OpenF1 fallback")
        return OpenF1Provider().fetch_session_raw(year,round_no,session)
    return None