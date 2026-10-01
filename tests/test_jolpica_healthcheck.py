import types
from api import jolpica_api as api
def test_healthcheck_returns_bool(monkeypatch):
    def mock_get(url,timeout=8):
        class R:
            status_code=200
            def json(self):return {"MRData":{}}
        return R()
    monkeypatch.setattr(api,"requests",types.SimpleNamespace(get=mock_get,RequestException=Exception))
    assert api.healthcheck() is True
def test_healthcheck_retries_on_failure(monkeypatch):
    call_count={"n":0}
    def mock_get(url,timeout=8):
        call_count["n"]+=1
        if call_count["n"]<2:raise Exception("Transient error")
        class R:
            status_code=200
            def json(self):return {"MRData":{}}
        return R()
    monkeypatch.setattr(api,"requests",types.SimpleNamespace(get=mock_get,RequestException=Exception))
    monkeypatch.setattr("time.sleep",lambda x:None)
    assert api.healthcheck() is True
    assert call_count["n"]==2