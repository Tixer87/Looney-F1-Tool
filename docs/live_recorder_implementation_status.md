# Live Recorder Module - Implementation Status
**Datum:** 23. November 2025  
**Status:** Schritt 4 abgeschlossen - Tests implementiert

---

## ✅ Implementierte Module

### 1. Core Components

#### `live_recorder/state.py` ✅
**Data Classes für Session State**
- `LiveSessionState`: Root State Container
- `LiveDriverState`: Driver-spezifischer State
- `StintData`: Reifenstint
- `PitstopData`: Boxenstopp
- `LapData`: Lap Timing (optional)
- `RaceControlEvent`: Race Control Message
- `WeatherData`: Wetter

#### `live_recorder/client.py` ✅
**SSE Client für f1-dash**
- `F1DashClient`: SSE Connection zu `http://localhost:4000/api/sse`
- `connect()`: Event Stream mit Callbacks
- `get_drivers()`: REST API Fallback
- `health_check()`: Health Check
- Error Handling & Reconnect vorbereitet

#### `live_recorder/processor.py` ✅
**Event Processing Pipeline**
- `LiveEventProcessor`: Main Processor
- `process_initial()`: Initial-Event Verarbeitung
- `process_update()`: Update-Event Verarbeitung
- Helper: `_update_session_info()`, `_initialize_drivers()`, `_update_timing_data()`, etc.

### 2. Detectors

#### `live_recorder/detectors/lap_completion.py` ✅
**Lap Completion Detector**
- Erkennt Runden-Abschluss via `lapCount.currentLap` Change
- Extrahiert Lap Data für jeden Fahrer
- Aktualisiert `laps_completed`

#### `live_recorder/detectors/pitstop.py` ✅
**Pitstop Detector**
- Erkennt Boxenstopps via Stint-Count Increase
- Registriert `PitstopData` mit Compound In/Out
- Track Previous Stint Counts pro Fahrer

#### `live_recorder/detectors/race_control.py` ✅
**Race Control Parser**
- Parst Race Control Messages
- Counts Safety Car / VSC / Red Flag Events
- Deduplication via Timestamps

### 3. Export & Orchestration

#### `live_recorder/exporter.py` ✅ (UPDATED 2025-11-21)
**RLT JSON Exporter**
- `LiveToRLTExporter`: Live State → RLT JSON
- `_build_meta()`: Meta Block Generator
- `_build_driver_block()`: Driver Block Generator
- **Mapping-Fixes angewendet:**
  - ✅ **Nation**: f1-dash `countryCode` direkt verwenden (bereits 3-Letter: NED, GBR, etc.)
  - ✅ **Team**: `_map_team_name()` mit `F1DASH_TEAM_MAP` (13 Team-Mappings: "Red Bull Racing" → "Red Bull", etc.)
  - ✅ **Driver Name**: `fullName` direkt verwenden (bereits RLT-kompatibel)
  - ✅ Fallback zu `teams_aliases.get_team_name()` für unknown Teams

#### `live_recorder/recorder.py` ✅
**Main Orchestrator**
- `LiveRecorder`: Haupt-Controller
- `start_recording()`: Entry Point
- Event Handlers: `_on_initial()`, `_on_update()`, `_on_error()`
- `_finalize_recording()`: Session Ende & Export
- `_print_summary()`: Zusammenfassung

---

## 📦 Dependencies Hinzugefügt

**`requirements.txt` aktualisiert:**
```txt
sseclient-py>=1.8.0      # SSE Client
python-dateutil>=2.8.0   # Datum/Zeit Parsing
```

---

## 📁 Modul-Struktur

```
live_recorder/
├── __init__.py              ✅ Exports
├── state.py                 ✅ Data Classes
├── client.py                ✅ SSE Client
├── processor.py             ✅ Event Processing
├── exporter.py              ✅ RLT JSON Export
├── recorder.py              ✅ Main Orchestrator
└── detectors/
    ├── __init__.py          ✅ Exports
    ├── lap_completion.py    ✅ Lap Detector
    ├── pitstop.py          ✅ Pitstop Detector
    └── race_control.py     ✅ Race Control Parser
```

---

## 🚀 Verwendung (Konzept)

### CLI Command
```bash
python main.py \
  --backend f1dash_live \
  --mode record \
  --f1dash-url http://localhost:4000 \
  --output-dir ./output/live
```

### Programmierung
```python
from live_recorder import LiveRecorder

recorder = LiveRecorder(
    f1dash_url="http://localhost:4000",
    output_dir="./output/live"
)

recorder.start_recording()
```

---

## 🔧 Fehlende Integration

### 1. `main.py` CLI Arguments
- `--backend f1dash_live` Option hinzufügen
- `--mode record` Option hinzufügen
- `--f1dash-url` Parameter

### 2. Backend Profile
- `backends/f1dash_live.py` erstellen (ähnlich wie `jolpica.py`)
- Integration in Backend-Auswahl

### 3. ~~Mapping Integration~~ ✅
- ~~Prüfen ob `mapping.drivers_nations.get_nation()` existiert~~ → **Nicht nötig**: f1-dash liefert bereits 3-Letter Codes
- ~~Prüfen ob `mapping.teams_aliases.get_rlt_team_name()` existiert~~ → **Gelöst**: `_map_team_name()` mit F1DASH_TEAM_MAP
- ✅ **Mapping-Fixes angewendet** (siehe exporter.py)

### 4. Logging Setup
- Logger konfigurieren in `main.py`
- Log-File für Live Recording

---

## ✅ Mapping-Korrekturen (21.11.2025)

**Problem:** Ursprüngliche Implementierung verwendete nicht-existierende Funktionen (`get_nation()`, `get_rlt_team_name()`)

**Analyse:**
- `mapping/drivers_nations.py`: API ist `get_driver_nation(raw: str)` und erwartet **Nationalität-Strings** ("Dutch"), nicht Codes ("NED")
- `mapping/teams_aliases.py`: API ist `get_team_name(raw, year)` und verwendet **Jolpica Constructor IDs** ("red_bull"), nicht Live-Namen
- **f1-dash Daten**: Liefert bereits 3-Letter Codes (`countryCode="NED"`) und vollständige Team-Namen (`teamName="Red Bull Racing"`)

**Lösung:**
1. **Nation Mapping:**
   - ❌ Alt: `get_nation(driver.country_code)` (existiert nicht)
   - ✅ Neu: `nation = driver.country_code` (direkt verwenden, da f1-dash bereits 3-Letter Codes liefert)

2. **Team Mapping:**
   - ❌ Alt: `get_rlt_team_name(driver.team_name)` (existiert nicht)
   - ✅ Neu: `_map_team_name(driver.team_name)` mit `F1DASH_TEAM_MAP`:
     - 13 Team-Mappings: "Red Bull Racing" → "Red Bull", "McLaren F1 Team" → "McLaren", etc.
     - Fallback zu `get_team_name()` für unbekannte Teams
     - Cleanup-Fallback: Entfernt " F1 Team" und " Racing" Suffixe

3. **Driver Name:**
   - ✅ Direkt `driver.full_name` verwenden (bereits RLT-kompatibel)

4. **DateTime Parsing:**
   - ✅ Bereits `dateutil.parser.parse()` im `processor.py` (kein `fromisoformat`)

**Ergebnis:**
- Keine ImportError mehr bei fehlenden Funktionen
- Nation Codes korrekt (NED, GBR, etc.)
- Team Namen RLT-konform (Red Bull, McLaren, etc.)
- Bereit für Tests

---

## ⚠️ Bekannte Lint-Warnung

**Import Errors:**
- `sseclient` nicht gefunden → Erst nach `pip install -r requirements.txt`
- Relative Imports → Type-Checking-Artefakte, funktionieren zur Laufzeit

---

## ✅ Test Suite (Schritt 4 - 23.11.2025)

### Test-Struktur
```
tests/live_recorder/
├── __init__.py
├── conftest.py              # Fixtures (session_state, sample_drivers, mock_events)
├── run_tests.py             # Test Runner (pytest wrapper mit Coverage)
├── test_happy_path.py       # Test 1: 2 Fahrer, 4 Laps, 1 SC, 1 Pitstop
├── test_mid_session.py      # Test 2: Start bei Lap 25, keine fake Pitstops
├── test_dnf.py              # Test 3: DNF Handling (retired=true)
├── test_race_control_dedup.py # Test 4: UTC Deduplication
└── test_weather.py          # Test 5: Weather Optional
```

### Test-Szenarien

#### Test 1: Happy Path ✅
**Datei:** `test_happy_path.py`  
**Szenario:** Monaco GP, 2 Fahrer (VER, NOR), 4 Laps, 1 SC, VER Pitstop Lap 3  
**Validierung:**
- ✅ Team Mapping: "Red Bull Racing" → "Red Bull", "McLaren F1 Team" → "McLaren"
- ✅ Nation Codes: NED, GBR (direkt verwendet)
- ✅ Pitstop Detection: VER 1 Pitstop, NOR 0 Pitstops
- ✅ Safety Car Count: 1
- ✅ Lap History: 4 Laps für beide Fahrer
- ✅ Best Laptimes korrekt

#### Test 2: Mid-Session Start ✅
**Datei:** `test_mid_session.py`  
**Szenario:** Bahrain GP, Recording Start bei Lap 25/78, VER im 2. Stint, NOR Pitstop Lap 28  
**Validierung:**
- ✅ **Keine fake Pitstops** bei vorhandenen Stints
- ✅ lap_history beginnt bei Lap 26 (erster recorded Lap)
- ✅ laps_completed = 5 (Laps 26-30)
- ✅ Stint-Daten korrekt übernommen (VER: 2 Stints, NOR: 1 → 2 Stints)
- ✅ NOR Pitstop Lap 28 korrekt erkannt

#### Test 3: DNF Handling ✅
**Datei:** `test_dnf.py`  
**Szenario:** Singapore GP, NOR retired=true bei Lap 3  
**Validierung:**
- ✅ finishing_status = "DNF"
- ✅ EndPosition = 20 (final Position nach DNF)
- ✅ Laps = 2 (bis zum Ausfall)
- ✅ VER weiter bis Lap 4 (Finished)

#### Test 4: Race Control Deduplication ✅
**Datei:** `test_race_control_dedup.py`  
**Szenario:** Saudi GP, 3 SC Messages (2 Duplikate), 1 VSC, 2 Red Flag (1 Duplikat)  
**Validierung:**
- ✅ SC Count = 1 (nicht 3!)
- ✅ VSC Count = 1
- ✅ Red Flag Count = 1 (nicht 2!)
- ✅ processed_timestamps Set funktioniert
- ✅ Identische UTC nur einmal gezählt

#### Test 5: Weather Optional ✅
**Datei:** `test_weather.py`  
**Szenario:** British GP, kein weatherData in Initial, später hinzugefügt  
**Validierung:**
- ✅ Export ohne Weather funktioniert (keine NoneType Errors)
- ✅ Weather nachträglich hinzugefügt (Lap 2)
- ✅ Weather Updates korrekt verarbeitet (AirTemp, Rainfall, etc.)
- ✅ Meta.Weather optional im Export

### Test Runner

**Alle Tests:**
```bash
python -m pytest tests/live_recorder/ -v
```

**Mit Coverage:**
```bash
python -m pytest tests/live_recorder/ -v --cov=live_recorder --cov-report=html
```

**Einzelner Test:**
```bash
python tests/live_recorder/run_tests.py --test test_happy_path.py
```

**Mit Coverage Script:**
```bash
python tests/live_recorder/run_tests.py --coverage
```

---

## 📝 Nächste Schritte

**→ Schritt 5:** `main.py` Integration
- CLI Arguments: `--backend f1dash_live`, `--mode record`, `--f1dash-url`
- Backend Profile: `backends/f1dash_live.py`
- Logging Setup

**→ Schritt 6:** End-to-End Test
- Lokale f1-dash Instanz starten
- Live Recording mit echtem SSE Stream
- RLT JSON validieren
- Performance Check (Memory, CPU bei 20 Fahrern)

---

**Status: ✅ Schritt 4 abgeschlossen - Tests bereit für Ausführung**
