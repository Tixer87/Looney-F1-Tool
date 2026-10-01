"""
Test 2: Mid-Session Start
Recording startet bei Lap 25 mit bereits existierenden Stints

Validierung:
- Keine fake Pitstops bei Session Start
- lap_history beginnt erst ab Lap 25
- Stint-Daten korrekt übernommen
"""

import pytest
from live_recorder.state import LiveSessionState
from live_recorder.processor import LiveEventProcessor
from live_recorder.exporter import LiveToRLTExporter


def test_mid_session_start():
    """
    Mid-Session Start: Recording beginnt bei Lap 25/78
    
    Szenario:
    - VER: Bereits im 2. Stint (SOFT → MEDIUM), P1
    - NOR: Noch im 1. Stint (SOFT), P2
    - Aufnahme läuft von Lap 25 bis 30
    - NOR macht Pitstop bei Lap 28
    
    Wichtig: KEINE fake Pitstops für vorhandene Stints generieren!
    """
    
    # === Setup ===
    # State wird aus Initial Event erstellt
    
    # === Initial Event bei Lap 25 ===
    initial_event = {
        "sessionInfo": {
            "meeting": {
                "name": "Bahrain Grand Prix",
                "location": "Sakhir",
                "country": {"name": "Bahrain", "code": "BH"}
            },
            "name": "Race",
            "type": "Race",
            "startDate": "2025-03-02T15:00:00Z"
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
                        {"Compound": "SOFT", "TotalLaps": 15, "New": "true"},
                        {"Compound": "MEDIUM", "TotalLaps": 9, "New": "true"}  # Aktueller Stint
                    ]
                },
                "4": {
                    "GridPos": "2",
                    "Stints": [
                        {"Compound": "SOFT", "TotalLaps": 24, "New": "true"}  # Noch im 1. Stint
                    ]
                }
            }
        },
        "lapCount": {
            "currentLap": 25,
            "totalLaps": 78
        },
        "timingData": {
            "Lines": {
                "1": {"Position": "1"},
                "4": {"Position": "2"}
            }
        }
    }
    
    # === Create State & Processor ===
    state = LiveEventProcessor.create_state_from_initial(initial_event)
    processor = LiveEventProcessor(state)
    processor.process_initial(initial_event)
    
    # === Validate Initial State ===
    assert state.current_lap == 25
    assert state.total_laps == 78
    
    ver = state.drivers["1"]
    nor = state.drivers["4"]
    
    # VER hat 2 Stints (15 + 9 Laps)
    assert len(ver.stints) == 2
    assert ver.stints[0].compound == "SOFT"
    assert ver.stints[0].total_laps == 15
    assert ver.stints[1].compound == "MEDIUM"
    assert ver.stints[1].total_laps == 9
    
    # NOR hat 1 Stint (24 Laps)
    assert len(nor.stints) == 1
    assert nor.stints[0].compound == "SOFT"
    assert nor.stints[0].total_laps == 24
    
    # WICHTIG: Keine Pitstops bei Initial!
    assert len(ver.pitstops) == 0, "Mid-Session Start darf keine fake Pitstops generieren!"
    assert len(nor.pitstops) == 0
    
    # Lap History ist leer (Recording beginnt jetzt)
    assert len(ver.lap_history) == 0
    assert len(nor.lap_history) == 0
    
    # === Lap 26 Complete ===
    update_lap26 = {
        "lapCount": {"currentLap": 26},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:32.456"}
                },
                "4": {
                    "Position": "2",
                    "LastLapTime": {"Value": "1:32.789"}
                }
            }
        }
    }
    
    processor.process_update(update_lap26)
    
    assert state.current_lap == 26
    assert ver.laps_completed == 1  # 1 Lap seit Recording Start
    assert nor.laps_completed == 1
    assert len(ver.lap_history) == 1
    assert ver.lap_history[0].lap_number == 26  # Absolute Lap Number
    
    # === Lap 27 Complete ===
    update_lap27 = {
        "lapCount": {"currentLap": 27},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:32.234"}
                },
                "4": {
                    "Position": "2",
                    "LastLapTime": {"Value": "1:32.567"}
                }
            }
        }
    }
    
    processor.process_update(update_lap27)
    
    assert state.current_lap == 27
    assert ver.laps_completed == 2
    assert nor.laps_completed == 2
    
    # === Lap 28 Complete + NOR Pitstop ===
    update_lap28_pitstop = {
        "lapCount": {"currentLap": 28},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:32.345"}
                },
                "4": {
                    "Position": "2",
                    "LastLapTime": {"Value": "1:55.123"}  # Pitstop Lap
                }
            }
        },
        "timingAppData": {
            "Lines": {
                "4": {
                    "Stints": [
                        {"Compound": "SOFT", "TotalLaps": 27, "New": "true"},
                        {"Compound": "MEDIUM", "TotalLaps": 0, "New": "true"}  # Neuer Stint
                    ]
                }
            }
        }
    }
    
    processor.process_update(update_lap28_pitstop)
    
    assert state.current_lap == 28
    assert nor.laps_completed == 3
    
    # NOR: Pitstop bei Lap 28 erkannt
    assert len(nor.pitstops) == 1
    pitstop = nor.pitstops[0]
    assert pitstop.lap == 28
    assert pitstop.compound_in == "SOFT"
    assert pitstop.compound_out == "MEDIUM"
    assert pitstop.stop_number == 1
    
    # VER: Immer noch keine Pitstops
    assert len(ver.pitstops) == 0
    
    # === Lap 29-30 Complete ===
    for lap in [29, 30]:
        update = {
            "lapCount": {"currentLap": lap},
            "timingData": {
                "Lines": {
                    "1": {"Position": "1", "LastLapTime": {"Value": f"1:32.{lap}"}},
                    "4": {"Position": "2", "LastLapTime": {"Value": f"1:32.{lap+100}"}}
                }
            }
        }
        processor.process_update(update)
    
    assert state.current_lap == 30
    assert ver.laps_completed == 5  # Laps 26-30
    assert nor.laps_completed == 5
    
    # === Freeze & Export ===
    state.freeze()
    exporter = LiveToRLTExporter(state)
    rlt_json = exporter.export()
    
    # === Validate RLT JSON ===
    drivers = rlt_json["Drivers"]
    
    ver_block = next(d for d in drivers if d["Number"] == "1")
    nor_block = next(d for d in drivers if d["Number"] == "4")
    
    # VER: Keine Pitstops während Recording
    assert len(ver_block["Pitstops"]) == 0
    assert ver_block["Laps"] == 5  # Nur recorded Laps
    
    # NOR: 1 Pitstop bei Lap 28
    assert len(nor_block["Pitstops"]) == 1
    assert nor_block["Pitstops"][0]["Lap"] == 28
    assert nor_block["Pitstops"][0]["Compound"] == "MEDIUM"
    assert nor_block["Laps"] == 5
    
    print("\n✅ Mid-Session Start Test bestanden!")
    print(f"   - Recording Start: Lap 25/78")
    print(f"   - VER Pitstops: {len(ver_block['Pitstops'])} (keine fake Pitstops!)")
    print(f"   - NOR Pitstops: {len(nor_block['Pitstops'])} (Lap 28)")
    print(f"   - Recorded Laps: VER={ver_block['Laps']}, NOR={nor_block['Laps']}")


if __name__ == "__main__":
    test_mid_session_start()
