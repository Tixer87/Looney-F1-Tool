from export.rlt_adapter import build_rlt_session
def test_rlt_no_session_wrapper():
    payload={
        "season":2025,
        "round":1,
        "session":"R",
        "circuit":"Melbourne",
        "Circuit":{"circuitName":"Melbourne"},
        "session_type":"Race",
        "race_type":"Main",
        "Drivers":[]
    }
    out=build_rlt_session(payload)
    assert "TrackName" in out
    assert "Drivers" in out
    assert "Session" not in out
def test_rlt_driver_ingame_name():
    payload={
        "season":2025,
        "round":1,
        "session":"R",
        "circuit":"Melbourne",
        "Circuit":{"circuitName":"Melbourne"},
        "session_type":"Race",
        "race_type":"Main",
        "Drivers":[{
            "DriverNumber":"1",
            "Driver":{"givenName":"Max","familyName":"Verstappen","nationality":"Dutch"},
            "Team":{"Name":"Red Bull Racing"},
            "Position":1,
            "Status":"Finished",
            "GridPosition":1,
            "SeatType":"Primary",
            "LapsCount":58,
            "PitsCount":2
        }]
    }
    out=build_rlt_session(payload)
    driver=out["Drivers"][0]
    assert "Driver" in driver
    assert driver["Driver"]["InGameName"]=="Max Verstappen"
    assert driver["Driver"]["Nationality"]=="Netherlands"
def test_rlt_racetype_main_default():
    payload={
        "season":2025,
        "round":1,
        "session":"R",
        "circuit":"Melbourne",
        "Circuit":{"circuitName":"Melbourne"},
        "session_type":"Race",
        "Drivers":[]
    }
    out=build_rlt_session(payload)
    assert out.get("RaceType")=="Regular"