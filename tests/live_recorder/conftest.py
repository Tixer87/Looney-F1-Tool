"""
Pytest Fixtures für Live Recorder Tests
"""

import pytest
from datetime import datetime
from live_recorder.state import LiveSessionState, LiveDriverState


def create_test_session_state(
    event_name="Monaco Grand Prix",
    circuit_name="Monaco",
    year=2025,
    session_type="Race"
):
    """
    Helper: Erstelle LiveSessionState mit required args
    """
    return LiveSessionState(
        session_key=1,
        session_name=session_type,
        session_type=session_type,
        event_name=event_name,
        circuit_key=1,
        circuit_name=circuit_name,
        country_name="Monaco",
        country_code="MCO",
        year=year,
        session_date=datetime(year, 5, 25, 14, 0, 0),
        gmt_offset="+02:00"
    )


@pytest.fixture
def basic_session_state():
    """
    Basis Session State für Tests
    """
    return create_test_session_state()


@pytest.fixture
def sample_driver_ver():
    """
    Sample Driver: Max Verstappen
    """
    driver = LiveDriverState(
        racing_number="1",
        tla="VER",
        full_name="Max Verstappen",
        team_name="Red Bull Racing",
        country_code="NED"
    )
    driver.grid_position = 1
    driver.current_position = 1
    return driver


@pytest.fixture
def sample_driver_nor():
    """
    Sample Driver: Lando Norris
    """
    driver = LiveDriverState(
        racing_number="4",
        tla="NOR",
        full_name="Lando Norris",
        team_name="McLaren F1 Team",
        country_code="GBR"
    )
    driver.grid_position = 2
    driver.current_position = 2
    return driver


@pytest.fixture
def mock_initial_event():
    """
    Mock f1-dash Initial Event
    """
    return {
        "sessionInfo": {
            "meeting": {
                "name": "Monaco Grand Prix",
                "location": "Monte Carlo",
                "country": {
                    "name": "Monaco"
                }
            },
            "name": "Race",
            "startDate": "2025-05-25T14:00:00Z"
        },
        "driverList": {
            "1": {
                "racingNumber": "1",
                "tla": "VER",
                "fullName": "Max Verstappen",
                "teamName": "Red Bull Racing",
                "countryCode": "NED"
            },
            "4": {
                "racingNumber": "4",
                "tla": "NOR",
                "fullName": "Lando Norris",
                "teamName": "McLaren F1 Team",
                "countryCode": "GBR"
            }
        },
        "timingAppData": {
            "Lines": {
                "1": {
                    "GridPos": "1",
                    "Stints": [
                        {"Compound": "SOFT", "TotalLaps": 0, "New": "true"}
                    ]
                },
                "4": {
                    "GridPos": "2",
                    "Stints": [
                        {"Compound": "SOFT", "TotalLaps": 0, "New": "true"}
                    ]
                }
            }
        },
        "lapCount": {
            "currentLap": 0,
            "totalLaps": 78
        },
        "trackStatus": {
            "Status": "1",
            "Message": ""
        }
    }


@pytest.fixture
def mock_update_lap_complete():
    """
    Mock f1-dash Update Event: Lap 1 Complete
    """
    return {
        "lapCount": {
            "currentLap": 1
        },
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:12.345"},
                    "BestLapTime": {"Value": "1:12.345"},
                    "Sectors": [
                        {"Value": "22.345"},
                        {"Value": "28.123"},
                        {"Value": "21.877"}
                    ]
                },
                "4": {
                    "Position": "2",
                    "LastLapTime": {"Value": "1:12.567"},
                    "BestLapTime": {"Value": "1:12.567"},
                    "Sectors": [
                        {"Value": "22.456"},
                        {"Value": "28.234"},
                        {"Value": "21.877"}
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_update_pitstop():
    """
    Mock f1-dash Update Event: VER macht Pitstop
    """
    return {
        "timingAppData": {
            "Lines": {
                "1": {
                    "Stints": [
                        {"Compound": "SOFT", "TotalLaps": 15, "New": "true"},
                        {"Compound": "MEDIUM", "TotalLaps": 0, "New": "true"}
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_update_safety_car():
    """
    Mock f1-dash Update Event: Safety Car
    """
    return {
        "trackStatus": {
            "Status": "4",
            "Message": "Safety Car"
        },
        "raceControlMessages": {
            "Messages": [
                {
                    "Utc": "2025-05-25T14:25:34Z",
                    "Message": "SAFETY CAR DEPLOYED"
                }
            ]
        }
    }


@pytest.fixture
def mock_update_dnf():
    """
    Mock f1-dash Update Event: NOR retired
    """
    return {
        "timingData": {
            "Lines": {
                "4": {
                    "Retired": True,
                    "Position": "20"
                }
            }
        }
    }
