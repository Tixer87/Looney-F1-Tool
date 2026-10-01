"""
Test 4: Race Control Deduplication
Duplicate UTC timestamps → nur einmal zählen

Validierung:
- SC/VSC/Red Flag Events mit identischem UTC nur einmal gezählt
- processed_timestamps Set funktioniert
- Mehrere verschiedene Events korrekt gezählt
"""

import pytest
from live_recorder.state import LiveSessionState
from live_recorder.processor import LiveEventProcessor
from live_recorder.exporter import LiveToRLTExporter


def test_race_control_deduplication():
    """
    Race Control Dedup: Duplicate UTC Timestamps
    
    Szenario:
    - Initial: 2 SC Messages mit identischem UTC
    - Update 1: Noch 1 SC Message mit identischem UTC (Duplikat)
    - Update 2: 1 VSC Message (neu)
    - Update 3: 1 Red Flag Message (neu)
    - Update 4: Nochmal Red Flag Message mit identischem UTC (Duplikat)
    
    Erwartung:
    - SC Count = 1 (nicht 3!)
    - VSC Count = 1
    - Red Flag Count = 1 (nicht 2!)
    """
    
    # === Setup ===
    # State wird aus Initial Event erstellt
    
    # === Initial Event mit 2 SC Messages (identischer UTC!) ===
    initial_event = {
        "sessionInfo": {
            "meeting": {
                "name": "Saudi Arabian Grand Prix",
                "location": "Jeddah",
                "country": {"name": "Saudi Arabia", "code": "SA"}
            },
            "name": "Race",
            "type": "Race",
            "startDate": "2025-03-09T18:00:00Z"
        },
        "driverList": {
            "1": {
                "racingNumber": "1",
                "tla": "VER",
                "fullName": "Max Verstappen",
                "teamName": "Red Bull Racing",
                "countryCode": "NED"
            }
        },
        "timingAppData": {
            "Lines": {
                "1": {"GridPos": "1", "Stints": [{"Compound": "SOFT", "TotalLaps": 0}]}
            }
        },
        "lapCount": {"currentLap": 0, "totalLaps": 50},
        "raceControlMessages": {
            "Messages": [
                {
                    "Utc": "2025-03-09T18:15:23.456Z",
                    "Message": "SAFETY CAR DEPLOYED"
                },
                {
                    "Utc": "2025-03-09T18:15:23.456Z",  # IDENTISCH!
                    "Message": "SAFETY CAR DEPLOYED"
                }
            ]
        }
    }
    
    # === Create State & Processor ===
    state = LiveEventProcessor.create_state_from_initial(initial_event)
    processor = LiveEventProcessor(state)
    processor.process_initial(initial_event)
    
    # Nur 1 SC gezählt (nicht 2!)
    assert state.safety_car_count == 1, f"Expected 1 SC, got {state.safety_car_count}"
    assert state.virtual_safety_car_count == 0
    assert state.red_flag_count == 0
    
    # processed_timestamps sollte 1 Eintrag haben
    assert len(processor.rc_parser.processed_timestamps) == 1
    
    # === Update 1: Noch eine SC Message mit identischem UTC (Duplikat) ===
    update_sc_dup = {
        "raceControlMessages": {
            "Messages": [
                {
                    "Utc": "2025-03-09T18:15:23.456Z",  # IDENTISCH zu Initial!
                    "Message": "SAFETY CAR DEPLOYED"
                }
            ]
        }
    }
    
    processor.process_update(update_sc_dup)
    
    # Immer noch nur 1 SC (Duplikat ignoriert)
    assert state.safety_car_count == 1, "Duplicate SC should be ignored"
    
    # === Update 2: VSC (neuer UTC) ===
    update_vsc = {
        "raceControlMessages": {
            "Messages": [
                {
                    "Utc": "2025-03-09T18:25:45.123Z",  # NEUER UTC
                    "Message": "VIRTUAL SAFETY CAR DEPLOYED"
                }
            ]
        }
    }
    
    processor.process_update(update_vsc)
    
    assert state.safety_car_count == 1
    assert state.virtual_safety_car_count == 1
    assert state.red_flag_count == 0
    
    # === Update 3: Red Flag (neuer UTC) ===
    update_red = {
        "raceControlMessages": {
            "Messages": [
                {
                    "Utc": "2025-03-09T18:35:12.789Z",  # NEUER UTC
                    "Message": "RED FLAG"
                }
            ]
        }
    }
    
    processor.process_update(update_red)
    
    assert state.safety_car_count == 1
    assert state.virtual_safety_car_count == 1
    assert state.red_flag_count == 1
    
    # === Update 4: Nochmal Red Flag mit identischem UTC (Duplikat) ===
    update_red_dup = {
        "raceControlMessages": {
            "Messages": [
                {
                    "Utc": "2025-03-09T18:35:12.789Z",  # IDENTISCH!
                    "Message": "RED FLAG"
                }
            ]
        }
    }
    
    processor.process_update(update_red_dup)
    
    # Immer noch nur 1 Red Flag (Duplikat ignoriert)
    assert state.red_flag_count == 1, "Duplicate Red Flag should be ignored"
    
    # === Freeze & Export ===
    state.freeze()
    exporter = LiveToRLTExporter(state)
    rlt_json = exporter.export()
    
    # === Validate RLT JSON ===
    race_control = rlt_json["Meta"]["RaceControl"]
    
    assert race_control["SafetyCar"] == 1, f"Expected 1 SC, got {race_control['SafetyCar']}"
    assert race_control["VSC"] == 1, f"Expected 1 VSC, got {race_control['VSC']}"
    assert race_control["RedFlag"] == 1, f"Expected 1 Red Flag, got {race_control['RedFlag']}"
    
    print("\n✅ Race Control Dedup Test bestanden!")
    print(f"   - Safety Car: {race_control['SafetyCar']} (2 Duplikate ignoriert)")
    print(f"   - VSC: {race_control['VSC']}")
    print(f"   - Red Flag: {race_control['RedFlag']} (1 Duplikat ignoriert)")
    print(f"   - processed_timestamps: {len(processor.rc_parser.processed_timestamps)} unique")


if __name__ == "__main__":
    test_race_control_deduplication()
