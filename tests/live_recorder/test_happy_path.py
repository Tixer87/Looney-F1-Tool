"""
Test 1: Happy Path
2 Fahrer, 3-4 Laps, 1 SC, 1 Pitstop

Validierung:
- Team Namen korrekt gemappt (Red Bull Racing → Red Bull, McLaren F1 Team → McLaren)
- Nation Codes direkt verwendet (NED, GBR)
- Pitstops korrekt erkannt (Lap, Compound, StopCount)
- SC Count = 1
"""

import pytest
from datetime import datetime
from live_recorder.state import LiveSessionState, LiveDriverState
from live_recorder.processor import LiveEventProcessor
from live_recorder.exporter import LiveToRLTExporter


def test_happy_path_full_race():
    """
    Happy Path: Komplettes Rennen mit 2 Fahrern über 4 Laps
    
    Szenario:
    - VER: P1 → P1, Pitstop Lap 3 (SOFT → MEDIUM), Best Lap 1:12.345
    - NOR: P2 → P2, keine Pitstops, Best Lap 1:12.567
    - 1 Safety Car Event nach Lap 2
    """
    
    # === Initial Event ===
    initial_event = {
        "sessionInfo": {
            "meeting": {
                "name": "Monaco Grand Prix",
                "location": "Monte Carlo",
                "country": {"name": "Monaco", "code": "MCO"}
            },
            "name": "Race",
            "type": "Race",
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
            "totalLaps": 4
        },
        "trackStatus": {
            "Status": "1",
            "Message": ""
        }
    }
    
    # === Create State & Processor ===
    state = LiveEventProcessor.create_state_from_initial(initial_event)
    processor = LiveEventProcessor(state)
    processor.process_initial(initial_event)
    
    # === Validate Initial State ===
    assert state.event_name == "Monaco Grand Prix"
    assert state.circuit_name == "Monte Carlo"
    assert state.session_type == "Race"
    assert state.total_laps == 4
    assert len(state.drivers) == 2
    
    ver = state.drivers["1"]
    nor = state.drivers["4"]
    
    assert ver.full_name == "Max Verstappen"
    assert ver.team_name == "Red Bull Racing"
    assert ver.country_code == "NED"
    assert ver.grid_position == 1
    
    assert nor.full_name == "Lando Norris"
    assert nor.team_name == "McLaren F1 Team"
    assert nor.country_code == "GBR"
    assert nor.grid_position == 2
    
    # === Lap 1 Complete ===
    update_lap1 = {
        "lapCount": {"currentLap": 1},
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
    
    processor.process_update(update_lap1)
    
    assert state.current_lap == 1
    assert ver.laps_completed == 1
    assert ver.best_laptime == "1:12.345"
    assert len(ver.lap_history) == 1
    assert ver.lap_history[0].laptime == "1:12.345"
    
    assert nor.laps_completed == 1
    assert nor.best_laptime == "1:12.567"
    
    # === Lap 2 Complete ===
    update_lap2 = {
        "lapCount": {"currentLap": 2},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:13.123"}
                },
                "4": {
                    "Position": "2",
                    "LastLapTime": {"Value": "1:13.456"}
                }
            }
        }
    }
    
    processor.process_update(update_lap2)
    
    assert state.current_lap == 2
    assert ver.laps_completed == 2
    assert nor.laps_completed == 2
    
    # === Safety Car nach Lap 2 ===
    update_sc = {
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
    
    processor.process_update(update_sc)
    
    assert state.track_status == "4"
    assert state.safety_car_count == 1
    
    # === Lap 3 Complete + VER Pitstop ===
    update_lap3_pitstop = {
        "lapCount": {"currentLap": 3},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:35.678"}  # langsam wegen Pitstop
                },
                "4": {
                    "Position": "2",
                    "LastLapTime": {"Value": "1:20.123"}  # unter SC
                }
            }
        },
        "timingAppData": {
            "Lines": {
                "1": {
                    "Stints": [
                        {"Compound": "SOFT", "TotalLaps": 3, "New": "true"},
                        {"Compound": "MEDIUM", "TotalLaps": 0, "New": "true"}
                    ]
                }
            }
        }
    }
    
    processor.process_update(update_lap3_pitstop)
    
    assert state.current_lap == 3
    assert ver.laps_completed == 3
    assert len(ver.pitstops) == 1
    
    pitstop = ver.pitstops[0]
    assert pitstop.lap == 3
    assert pitstop.compound_in == "SOFT"
    assert pitstop.compound_out == "MEDIUM"
    assert pitstop.stop_number == 1
    
    # === Lap 4 Complete (Finish) ===
    update_lap4 = {
        "lapCount": {"currentLap": 4},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:12.789"}
                },
                "4": {
                    "Position": "2",
                    "LastLapTime": {"Value": "1:13.012"}
                }
            }
        }
    }
    
    processor.process_update(update_lap4)
    
    assert state.current_lap == 4
    assert ver.laps_completed == 4
    assert nor.laps_completed == 4
    
    # === Freeze State & Export ===
    state.freeze()
    exporter = LiveToRLTExporter(state)
    rlt_json = exporter.export()
    
    # === Validate RLT JSON ===
    
    # Meta Block
    meta = rlt_json["Meta"]
    assert meta["Event"] == "Monaco Grand Prix"
    assert meta["Track"] == "Monte Carlo"
    assert meta["Year"] == 2025
    assert meta["Session"] == "Race"
    assert meta["RaceControl"]["SafetyCar"] == 1
    assert meta["RaceControl"]["VSC"] == 0
    assert meta["RaceControl"]["RedFlag"] == 0
    
    # Driver Blocks
    drivers = rlt_json["Drivers"]
    assert len(drivers) == 2
    
    # VER Block
    ver_block = next(d for d in drivers if d["Number"] == "1")
    assert ver_block["Name"] == "Max Verstappen"
    assert ver_block["Team"] == "Red Bull"  # Gemappt!
    assert ver_block["Nation"] == "NED"  # Direkt!
    assert ver_block["StartPosition"] == 1
    assert ver_block["EndPosition"] == 1
    assert ver_block["Laps"] == 4
    assert ver_block["BestLaptime"] == "1:12.345"
    assert len(ver_block["Pitstops"]) == 1
    assert ver_block["Pitstops"][0]["Lap"] == 3
    assert ver_block["Pitstops"][0]["Compound"] == "MEDIUM"
    assert ver_block["Pitstops"][0]["StopCount"] == 1
    
    # NOR Block
    nor_block = next(d for d in drivers if d["Number"] == "4")
    assert nor_block["Name"] == "Lando Norris"
    assert nor_block["Team"] == "McLaren"  # Gemappt!
    assert nor_block["Nation"] == "GBR"  # Direkt!
    assert nor_block["StartPosition"] == 2
    assert nor_block["EndPosition"] == 2
    assert nor_block["Laps"] == 4
    assert nor_block["BestLaptime"] == "1:12.567"
    assert len(nor_block["Pitstops"]) == 0
    
    print("\n✅ Happy Path Test bestanden!")
    print(f"   - Teams korrekt gemappt: Red Bull Racing → {ver_block['Team']}, McLaren F1 Team → {nor_block['Team']}")
    print(f"   - Nations direkt: VER={ver_block['Nation']}, NOR={nor_block['Nation']}")
    print(f"   - Pitstops: VER={len(ver_block['Pitstops'])}, NOR={len(nor_block['Pitstops'])}")
    print(f"   - Safety Car Count: {meta['RaceControl']['SafetyCar']}")


if __name__ == "__main__":
    test_happy_path_full_race()
