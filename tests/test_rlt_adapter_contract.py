from export.rlt_adapter import build_rlt_session

def test_rlt_no_session_wrapper():
    """Nach deinem Fix: KEIN 'Session'-Wrapper"""
    payload = {
        "season": 2025,
        "round": 1,
        "session": "R",
        "circuit": "Melbourne",
        "Circuit": {"circuitName": "Melbourne"},
        "session_type": "Race",
        "race_type": "Main",
        "Drivers": []
    }
    out = build_rlt_session(payload)
    # Top-Level-Felder direkt, kein {"Session": ...} wrapper
    assert "TrackName" in out
    assert "Drivers" in out
    assert "Session" not in out  # Kritisch: kein wrapper!

def test_rlt_driver_ingame_name():
    """Driver hat InGameName, nicht Nationality"""
    payload = {
        "season": 2025,
        "round": 1,
        "session": "R",
        "circuit": "Melbourne",
        "Circuit": {"circuitName": "Melbourne"},
        "session_type": "Race",
        "race_type": "Main",
        "Drivers": [{
            "DriverNumber": "1",
            "Driver": {"givenName": "Max", "familyName": "Verstappen"},
            "Team": {"Name": "Red Bull Racing"},
            "Position": 1,
            "Status": "Finished",
            "GridPosition": 1,
            "SeatType": "Primary",
            "LapsCount": 58,
            "PitsCount": 2
        }]
    }
    out = build_rlt_session(payload)
    driver = out["Drivers"][0]
    assert "Driver" in driver
    assert "InGameName" in driver["Driver"]
    assert "Nationality" not in driver["Driver"]  # Kritisch: kein Nationality!

def test_rlt_racetype_main_default():
    """RaceType default ist 'Main', nicht 'Regular'"""
    payload = {
        "season": 2025,
        "round": 1,
        "session": "R",
        "circuit": "Melbourne",
        "Circuit": {"circuitName": "Melbourne"},
        "session_type": "Race",
        "Drivers": []
    }
    out = build_rlt_session(payload)
    assert out.get("RaceType") == "Main"
