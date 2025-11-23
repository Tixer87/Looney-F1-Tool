"""
Test 5: Weather Optional
weatherData nicht in initial, später hinzugefügt

Validierung:
- Export funktioniert ohne Weather
- Weather kann nachträglich hinzugefügt werden
- Keine NoneType Errors bei fehlendem Weather
"""

import pytest
from live_recorder.state import LiveSessionState
from live_recorder.processor import LiveEventProcessor
from live_recorder.exporter import LiveToRLTExporter


def test_weather_optional():
    """
    Weather Optional: weatherData fehlt initial, wird später hinzugefügt
    
    Szenario:
    - Initial: Kein weatherData
    - Update 1: Lap 1, immer noch kein Weather
    - Update 2: Lap 2, weatherData hinzugefügt
    - Update 3: Lap 3, Weather aktualisiert
    
    Validierung:
    - Export funktioniert mit und ohne Weather
    - Keine NoneType Errors
    - Weather im Meta Block optional
    """
    
    # === Setup ===
    # State wird aus Initial Event erstellt
    
    # === Initial Event OHNE weatherData ===
    initial_event = {
        "sessionInfo": {
            "meeting": {
                "name": "British Grand Prix",
                "location": "Silverstone",
                "country": {"name": "United Kingdom", "code": "GB"}
            },
            "name": "Race",
            "type": "Race",
            "startDate": "2025-07-06T14:00:00Z"
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
        "lapCount": {"currentLap": 0, "totalLaps": 3}
        # KEIN weatherData!
    }
    
    # === Create State & Processor ===
    state = LiveEventProcessor.create_state_from_initial(initial_event)
    processor = LiveEventProcessor(state)
    processor.process_initial(initial_event)
    
    # Weather sollte None sein
    assert state.weather is None
    
    # === Update 1: Lap 1, immer noch kein Weather ===
    update_lap1 = {
        "lapCount": {"currentLap": 1},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:27.123"}
                }
            }
        }
        # KEIN weatherData!
    }
    
    processor.process_update(update_lap1)
    
    assert state.current_lap == 1
    assert state.weather is None
    
    # === Export ohne Weather sollte funktionieren ===
    state_snapshot = state
    exporter_no_weather = LiveToRLTExporter(state_snapshot)
    rlt_json_no_weather = exporter_no_weather.export()
    
    # Meta Block sollte existieren, Weather optional
    assert "Meta" in rlt_json_no_weather
    meta_no_weather = rlt_json_no_weather["Meta"]
    
    # Weather sollte None oder leer sein
    weather_value = meta_no_weather.get("Weather")
    assert weather_value is None or weather_value == "", f"Weather should be None or empty, got: {weather_value}"
    
    print("\n✅ Export ohne Weather erfolgreich!")
    
    # === Update 2: Lap 2, weatherData hinzugefügt ===
    update_lap2_weather = {
        "lapCount": {"currentLap": 2},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:27.234"}
                }
            }
        },
        "weatherData": {
            "AirTemp": "22",
            "Humidity": "65",
            "Pressure": "1013",
            "Rainfall": "0",
            "TrackTemp": "35",
            "WindDirection": "180",
            "WindSpeed": "5"
        }
    }
    
    processor.process_update(update_lap2_weather)
    
    assert state.current_lap == 2
    assert state.weather is not None
    assert state.weather.air_temp == "22"
    assert state.weather.track_temp == "35"
    assert state.weather.humidity == "65"
    
    # === Update 3: Lap 3, Weather aktualisiert ===
    update_lap3_weather = {
        "lapCount": {"currentLap": 3},
        "timingData": {
            "Lines": {
                "1": {
                    "Position": "1",
                    "LastLapTime": {"Value": "1:27.345"}
                }
            }
        },
        "weatherData": {
            "AirTemp": "21",
            "Humidity": "70",
            "Pressure": "1012",
            "Rainfall": "1",  # Regen beginnt!
            "TrackTemp": "33",
            "WindDirection": "190",
            "WindSpeed": "8"
        }
    }
    
    processor.process_update(update_lap3_weather)
    
    assert state.current_lap == 3
    assert state.weather.air_temp == "21"
    assert state.weather.rainfall == True  # rainfall ist bool: "1" → True
    assert state.weather.wind_speed == "8"
    
    # === Freeze & Export mit Weather ===
    state.freeze()
    exporter = LiveToRLTExporter(state)
    rlt_json = exporter.export()
    
    # === Validate RLT JSON mit Weather ===
    meta = rlt_json["Meta"]
    
    # Weather sollte jetzt vorhanden sein
    weather = meta.get("Weather")
    assert weather is not None, "Weather should be present after update"
    
    # Weather könnte String oder Dict sein, je nach Exporter-Logik
    # Für RLT ist Weather oft ein String oder ein strukturiertes Objekt
    print(f"\n✅ Export mit Weather erfolgreich!")
    print(f"   - Weather Type: {type(weather)}")
    print(f"   - Weather Value: {weather}")
    
    # Drivers sollten unabhängig von Weather funktionieren
    drivers = rlt_json["Drivers"]
    assert len(drivers) == 1
    ver_block = drivers[0]
    assert ver_block["Name"] == "Max Verstappen"
    assert ver_block["Laps"] == 3
    
    print(f"   - Driver Laps: {ver_block['Laps']}")
    print(f"   - Weather hatte KEINEN Einfluss auf Driver Export")


def test_weather_completely_absent():
    """
    Edge Case: Weather komplett abwesend, auch in Updates
    """
    
    initial = {
        "sessionInfo": {
            "meeting": {"name": "Test GP", "location": "Test", "country": {"name": "Test", "code": "XX"}},
            "name": "Race",
            "type": "Race",
            "startDate": "2025-01-01T12:00:00Z"
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
            "Lines": {"1": {"GridPos": "1", "Stints": [{"Compound": "SOFT", "TotalLaps": 0}]}}
        },
        "lapCount": {"currentLap": 0, "totalLaps": 1}
    }
    
    # === Create State & Processor ===
    state = LiveEventProcessor.create_state_from_initial(initial)
    processor = LiveEventProcessor(state)
    processor.process_initial(initial)
    
    update = {
        "lapCount": {"currentLap": 1},
        "timingData": {"Lines": {"1": {"Position": "1", "LastLapTime": {"Value": "1:30.000"}}}}
    }
    
    processor.process_update(update)
    
    state.freeze()
    exporter = LiveToRLTExporter(state)
    rlt_json = exporter.export()
    
    # Sollte ohne Fehler exportieren
    assert "Meta" in rlt_json
    assert "Drivers" in rlt_json
    
    weather = rlt_json["Meta"].get("Weather")
    assert weather is None or weather == ""
    
    print("\n✅ Export komplett ohne Weather erfolgreich!")


if __name__ == "__main__":
    test_weather_optional()
    test_weather_completely_absent()
