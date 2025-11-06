import types
from api.providers import jolpica_api as api

def test_healthcheck_returns_bool(monkeypatch):
    def mock_get(url, timeout=8):
        class R: 
            status_code = 200
            def json(self): return {"MRData": {}}
        return R()
    
    mock_requests = types.SimpleNamespace(
        get=mock_get,
        RequestException=Exception
    )
    monkeypatch.setattr(api, "requests", mock_requests)
    assert api.healthcheck() is True

def test_healthcheck_retries_on_failure(monkeypatch):
    call_count = {"n": 0}
    
    def mock_get(url, timeout=8):
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise Exception("Transient error")
        class R: 
            status_code = 200
            def json(self): return {"MRData": {}}
        return R()
    
    mock_requests = types.SimpleNamespace(
        get=mock_get,
        RequestException=Exception
    )
    monkeypatch.setattr(api, "requests", mock_requests)
    monkeypatch.setattr("time.sleep", lambda x: None)  # Skip sleep
    assert api.healthcheck() is True
    assert call_count["n"] == 2  # Failed once, succeeded on retry
