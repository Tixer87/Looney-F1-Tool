from api.providers.router import get_provider, FastF1ProviderWrapper
from api.providers.jolpica_provider import JolpicaProvider

def test_router_prefers_jolpica(monkeypatch):
    monkeypatch.setattr(JolpicaProvider, "is_available", lambda self: True)
    p = get_provider()
    assert isinstance(p, JolpicaProvider)

def test_router_falls_back_to_fastf1(monkeypatch):
    monkeypatch.setattr(JolpicaProvider, "is_available", lambda self: False)
    p = get_provider()
    assert isinstance(p, FastF1ProviderWrapper)

def test_router_prefer_fastf1_direct():
    p = get_provider(prefer="fastf1")
    assert isinstance(p, FastF1ProviderWrapper)
