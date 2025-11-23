"""
Test 3: DNF Handling
Driver retired=true → finishing_status="DNF"

Validierung:
- finishing_status korrekt gesetzt
- EndPosition aus final Position (nicht current während Rennen)
- Laps bis zum Ausfall gezählt
"""

import pytest
from live_recorder.state import LiveSessionState
from live_recorder.processor import LiveEventProcessor
from live_recorder.exporter import LiveToRLTExporter


def test_dnf_handling():
    """
    DNF Handling: NOR fällt bei Lap 3 aus
    
    Szenario:
    - VER: Fährt bis Lap 4 (Finish)
    - NOR: DNF bei Lap 3 (retired=true)
    
    Validierung:
    - NOR finishing_status = "DNF"
    - NOR EndPosition = final Position (nicht current während Rennen)
    - NOR Laps = 2 (bis zum Ausfall)
    """
    
    # === Setup ===
    # State wird aus Initial Event erstellt
    
    # === Initial Event ===
    initial_event = {
        "sessionInfo": {
            "meeting": {
                "name": "Singapore Grand Prix",
                "location": "Marina Bay",
                "country": {"name": "Singapore", "code": "SG"}
            },
            "name": "Race",
            "type": "Race",
            "startDate": "2025-09-21T12:00:00Z"
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
                "1": {"GridPos": "1", "Stints": [{"Compound": "SOFT", "TotalLaps": 0}]},
                "4": {"GridPos": "2", "Stints": [{"Compound": "SOFT", "TotalLaps": 0}]}
            }
        },
        "lapCount": {"currentLap": 0, "totalLaps": 4}
    }
    
    # === Create State & Processor ===
    state = LiveEventProcessor.create_state_from_initial(initial_event)
    processor = LiveEventProcessor(state)
    processor.process_initial(initial_event)
    
    ver = state.drivers["1"]
    nor = state.drivers["4"]
    
    # === Lap 1 Complete ===
    update_lap1 = {
        "lapCount": {"currentLap": 1},
        "timingData": {
            "Lines": {
                "1": {"Position": "1", "LastLapTime": {"Value": "1:45.123"}},
                "4": {"Position": "2", "LastLapTime": {"Value": "1:45.456"}}
            }
        }
    }
    
    processor.process_update(update_lap1)
    
    assert ver.laps_completed == 1
    assert nor.laps_completed == 1
    assert nor.retired is False
    
    # === Lap 2 Complete ===
    update_lap2 = {
        "lapCount": {"currentLap": 2},
        "timingData": {
            "Lines": {
                "1": {"Position": "1", "LastLapTime": {"Value": "1:45.234"}},
                "4": {"Position": "2", "LastLapTime": {"Value": "1:45.567"}}
            }
        }
    }
    
    processor.process_update(update_lap2)
    
    assert ver.laps_completed == 2
    assert nor.laps_completed == 2
    
    # === Lap 3: NOR retired ===
    update_lap3_dnf = {
        "lapCount": {"currentLap": 3},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:45.345"}
                },
                "4": {
                    "Position": "20",  # Fällt nach hinten
                    "Retired": True,
                    "LastLapTime": {"Value": ""}  # Kein Laptime mehr
                }
            }
        }
    }
    
    processor.process_update(update_lap3_dnf)
    
    assert state.current_lap == 3
    assert ver.laps_completed == 3
    assert nor.laps_completed == 2  # Lap 3 nicht mehr abgeschlossen
    assert nor.retired is True
    assert nor.current_position == 20
    
    # === Lap 4 Complete (VER finishes) ===
    update_lap4 = {
        "lapCount": {"currentLap": 4},
        "timingData": {
            "Lines": {
                "1": {"Position": "1", "LastLapTime": {"Value": "1:45.456"}}
            }
        }
    }
    
    processor.process_update(update_lap4)
    
    assert ver.laps_completed == 4
    assert nor.laps_completed == 2  # Immer noch 2
    
    # === Freeze & Export ===
    state.freeze()
    exporter = LiveToRLTExporter(state)
    rlt_json = exporter.export()
    
    # === Validate RLT JSON ===
    drivers = rlt_json["Drivers"]
    
    ver_block = next(d for d in drivers if d["Number"] == "1")
    nor_block = next(d for d in drivers if d["Number"] == "4")
    
    # VER: Finished
    assert ver_block["Status"] == "Finished"
    assert ver_block["EndPosition"] == 1
    assert ver_block["Laps"] == 4
    
    # NOR: DNF
    assert nor_block["Status"] == "DNF"
    assert nor_block["EndPosition"] == 20  # Final Position nach DNF
    assert nor_block["Laps"] == 2  # Nur 2 Laps abgeschlossen
    
    print("\n✅ DNF Handling Test bestanden!")
    print(f"   - VER: Status={ver_block['Status']}, Laps={ver_block['Laps']}, EndPos={ver_block['EndPosition']}")
    print(f"   - NOR: Status={nor_block['Status']}, Laps={nor_block['Laps']}, EndPos={nor_block['EndPosition']}")


if __name__ == "__main__":
    test_dnf_handling()
