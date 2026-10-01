# Live Recorder Test Suite

Alle Tests für das Live Recorder Module mit den 5 kritischen Szenarien.

## Quick Start

### Alle Tests ausführen
```bash
python -m pytest tests/live_recorder/ -v
```

### Mit Coverage Report
```bash
python -m pytest tests/live_recorder/ -v --cov=live_recorder --cov-report=html
```

### Einzelner Test
```bash
python -m pytest tests/live_recorder/test_happy_path.py -v -s
```

### Mit Test Runner Script
```bash
# Alle Tests
python tests/live_recorder/run_tests.py

# Mit Coverage
python tests/live_recorder/run_tests.py --coverage

# Einzelner Test
python tests/live_recorder/run_tests.py --test test_happy_path.py
```

## Test-Szenarien

| Test | Datei | Beschreibung | Key Checks |
|------|-------|--------------|------------|
| **Test 1** | `test_happy_path.py` | 2 Fahrer, 4 Laps, 1 SC, 1 Pitstop | Team/Nation Mapping, Pitstop Detection, SC Count |
| **Test 2** | `test_mid_session.py` | Recording Start bei Lap 25/78 | Keine fake Pitstops, korrekte lap_history |
| **Test 3** | `test_dnf.py` | DNF Handling (retired=true) | finishing_status="DNF", EndPosition korrekt |
| **Test 4** | `test_race_control_dedup.py` | UTC Deduplication | SC/VSC/Red Flag nur einmal gezählt |
| **Test 5** | `test_weather.py` | Weather Optional | Export ohne Weather, nachträgliches Hinzufügen |

## Fixtures (conftest.py)

- `basic_session_state()`: Basis LiveSessionState
- `sample_driver_ver()`: Max Verstappen (Red Bull Racing, NED)
- `sample_driver_nor()`: Lando Norris (McLaren F1 Team, GBR)
- `mock_initial_event()`: f1-dash Initial Event
- `mock_update_lap_complete()`: Lap Complete Event
- `mock_update_pitstop()`: Pitstop Event
- `mock_update_safety_car()`: Safety Car Event
- `mock_update_dnf()`: DNF Event

## Erwartete Ergebnisse

### Test 1: Happy Path
```
✅ Teams korrekt gemappt: Red Bull Racing → Red Bull, McLaren F1 Team → McLaren
✅ Nations direkt: VER=NED, NOR=GBR
✅ Pitstops: VER=1, NOR=0
✅ Safety Car Count: 1
```

### Test 2: Mid-Session Start
```
✅ Recording Start: Lap 25/78
✅ VER Pitstops: 0 (keine fake Pitstops!)
✅ NOR Pitstops: 1 (Lap 28)
✅ Recorded Laps: VER=5, NOR=5
```

### Test 3: DNF Handling
```
✅ VER: Status=Finished, Laps=4, EndPos=1
✅ NOR: Status=DNF, Laps=2, EndPos=20
```

### Test 4: Race Control Dedup
```
✅ Safety Car: 1 (2 Duplikate ignoriert)
✅ VSC: 1
✅ Red Flag: 1 (1 Duplikat ignoriert)
```

### Test 5: Weather Optional
```
✅ Export ohne Weather erfolgreich
✅ Export mit Weather erfolgreich
✅ Weather hatte KEINEN Einfluss auf Driver Export
```

## Dependencies

```bash
pip install pytest pytest-cov
```

Bereits in `requirements.txt`:
- `sseclient-py>=1.8.0`
- `python-dateutil>=2.8.0`

## Troubleshooting

**Import Errors:**
- Stelle sicher, dass du im Workspace Root bist
- `pip install -r requirements.txt`

**Test Failures:**
- Check `live_recorder/` Module sind alle vorhanden
- Check `mapping/` Module existieren (drivers_nations, teams_aliases)

**Coverage zu niedrig:**
- Tests decken Core-Funktionalität ab (state, processor, detectors, exporter)
- `client.py` und `recorder.py` benötigen Live f1-dash für vollständige Tests
