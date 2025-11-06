# Entry-Points & Hauptausführungspfade

**Audit-Datum:** 01.11.2025  
**Zweck:** Dokumentation aller Einstiegspunkte ins Programm

---

## 1. CLI Entry-Point: `main.py`

### Startpfad
```bash
python main.py [--season YEAR] [--round ROUND] [--session SESSION] [--outdir PATH]
```

### Hauptfunktionen

#### `print_welcome_banner()` (Zeilen 60-100)
**Zweck:** Visuelles Banner beim CLI-Start  
**Implementierung:**
- **Primary:** Rich-Library (colored ASCII Art, Links, Panels)
- **Fallback:** Plain-Text Print bei fehlendem Rich-Modul

**Ausgabe:**
- ASCII-Logo "LOONEY F1"
- Version-Info (v1.6)
- Community-Links (GitHub Sponsors)
- Charakter-Zitate (Bugs Bunny, Road Runner, Kermit)

#### `export_session()` (Zeilen 17-46)
**Signatur:**
```python
def export_session(year, round_number, endpoint, quali_phase=None, outdir=None)
```

**Ablauf:**
1. Session-Type-Mapping (`endpoint` → "Qualification"/"Sprint"/"Race")
2. `build_session_metadata()` - Core-Modul
3. `build_driver_blocks()` - Core-Modul
4. Dateiname-Generierung (round-basiert, alt)
5. `export_rlt_json()` - Export-Modul
6. Erfolgs-/Fehler-Feedback

**Legacy-Hinweis:** Verwendet altes Filename-Schema (vor Circuit-Namen-Update)

#### `list_races()` (Zeilen 48-58)
**Zweck:** Rennkalender für gegebenes Jahr abrufen  
**API-Call:** `https://api.jolpi.ca/ergast/f1/{year}.json`  
**Return:** Liste von Race-Dictionaries

**Beispiel-Output:**
```python
[
  {"season": "2024", "round": "1", "raceName": "Bahrain Grand Prix", ...},
  ...
]
```

#### `main()` CLI-Workflow (Zeilen 101-End)
**Argparse-Parameter:**
- `--season` / `-s` - Jahr (Default aus `config.json`)
- `--round` / `-r` - Rundennummer
- `--session` - Session-Type (Q1/Q2/Q3/R/etc.)
- `--outdir` / `-o` - Export-Pfad (Default: `rlt-ready/`)

**Ablauflogik:**
1. Welcome-Banner
2. Config-Loader für Defaults
3. Argument-Parsing
4. Rennkalender-Abruf (optional: List-Modus)
5. `export_session()` mit validierten Parametern
6. Exit mit Status-Code

**Verwendete Imports:**
- `api.jolpica_api` (Legacy: `get_season_drivers`, `fetch_race_data`)
- `core.session_builder.build_session_metadata`
- `core.driver_block.build_driver_blocks`
- `export.rlt_exporter.export_rlt_json`
- `utils.config_loader` (Defaults)

---

## 2. GUI Entry-Point: `gui_app.py`

### Startpfad
```bash
python gui_app.py
# oder:
LooneyF1Tool.exe
```

### Hauptklassen & Komponenten

#### `CalendarWindow` (Zeilen 8-200+)
**Zweck:** Interaktiver Rennkalender mit Export-Menü

**Initialisierung:**
```python
def __init__(self, parent_gui, season=2025)
```

**GUI-Struktur:**
- **Treeview:** 4 Spalten (Round | Date | Grand Prix | Circuit)
- **Search Bar:** Filter-Funktion für Rennkalender
- **Context Menu:** Rechtsklick → Export Practice/Quali/Sprint/Race
- **Bulk-Option:** "Export All Sessions"

**Key Methods:**
- `load_schedule()` - Lädt Kalender via `schedule_with_fallback()`
- `populate_tree()` - Füllt Treeview mit Renndaten
- `on_double_click()` - Doppelklick-Event-Handler
- `on_right_click()` - Rechtsklick-Menü
- `export_session()` - Triggert Export via `run_export()`
- `_fmt_date()` - Formatierung zu DD.MM.YYYY

**Provider-Integration:**
```python
from api.providers.router import schedule_with_fallback
```

#### `MainGUI` / Main Application Window (Zeilen 200+)
**Komponenten:**

1. **Season-Picker** (Dropdown)
   - Jahresauswahl (2020-2025+)
   - Aktualisiert verfügbare Runden

2. **Round-Picker** (Dropdown)
   - Rundennummer (1-24)
   - Dynamisch geladen aus Schedule

3. **Session-Picker** (Dropdown)
   - Optionen: "Practice", "Qualifying", "Sprint", "Race", "All Sessions"
   - Mapping via `export_service.expand_session_group()`

4. **Export-Button**
   - Triggert `run_export()` im Background-Thread
   - Progress-Indikator (optional)

5. **LogView** (Custom Widget)
   - Color-coded Log-Levels:
     - 🔵 INFO (blau)
     - 🟢 STEP (grün)
     - 🟡 WARN (orange)
     - 🔴 ERROR (rot)
     - ✅ DONE (dunkelgrün)
   - ScrolledText-Widget für automatisches Scrolling

6. **Output-Directory-Picker**
   - Button → File-Dialog
   - Default: `%USERPROFILE%\Documents\RLT`

**Threading:**
```python
export_thread = threading.Thread(target=self.export_worker, daemon=True)
export_thread.start()
```
→ Verhindert UI-Freeze während langer Exporte

#### Export-Worker-Funktion
**Ablauf:**
1. Session-Group expandieren (`expand_session_group()`)
2. Für jede Session: `run_export(season, round, session, outdir)`
3. Logging zu GUI via Queue oder Direct-Call
4. Fehlerbehandlung mit Try-Catch
5. Success/Failure-Feedback

**Verwendete Module:**
```python
from api.export_service import run_export, expand_session_group
from api.providers.router import schedule_with_fallback
```

---

## 3. PyInstaller Entry-Point: `LooneyF1Tool.spec`

### Build-Konfiguration

**Entry-Script:** `gui_app.py`

**Analysis-Phase:**
```python
a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[('mapping', 'mapping'), ('config.json', '.')],
    hiddenimports=['fastf1.events', 'fastf1.api', 'fastf1.core', 'pandas'],
    ...
)
```

**Bundle-Daten:**
- `mapping/` → alle JSON-Ressourcen
- `config.json` → Root-Level

**Hidden-Imports:**
- `fastf1.events`, `fastf1.api`, `fastf1.core` (dynamische Imports)
- `pandas` (DataFrame-Engine)

**EXE-Konfiguration:**
```python
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # → onedir-Modus
    name='LooneyF1Tool',
    console=False,          # → Windowed (kein CMD-Fenster)
    upx=True,               # → UPX-Kompression
    ...
)
```

**COLLECT-Phase:**
```python
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='LooneyF1Tool',  # → dist/LooneyF1Tool/ Ordner
)
```

**Output-Struktur:**
```
dist/
└── LooneyF1Tool/
    ├── LooneyF1Tool.exe
    └── _internal/
        ├── base_library.zip
        ├── python313.dll
        ├── mapping/
        ├── config.json
        └── [viele .pyd, .dll Dateien]
```

---

## 4. Programm-Ablauf: Typische Ausführungspfade

### Pfad A: CLI-Export (Einzelne Session)
```
main.py
 └─> print_welcome_banner()
 └─> argparse → Parameter
 └─> export_session(year, round, endpoint)
      ├─> build_session_metadata() [core/session_builder.py]
      ├─> build_driver_blocks() [core/driver_block.py]
      │    └─> jolpica_api / providers → Daten abrufen
      └─> export_rlt_json() [export/rlt_exporter.py]
           └─> JSON-Datei schreiben
```

### Pfad B: GUI-Export (Calendar-Workflow)
```
gui_app.py
 └─> MainGUI.__init__()
 └─> "Show Calendar" Button
      └─> CalendarWindow.__init__()
           ├─> load_schedule() → schedule_with_fallback()
           │    ├─> jolpica_provider.schedule(2025)
           │    └─> (fallback) fastf1_provider.schedule(2025)
           └─> populate_tree()
 
[User: Rechtsklick auf Rennen → "Export Race"]
 └─> export_session(session_code)
      └─> Threading → export_worker()
           └─> run_export() [api/export_service.py]
                ├─> build_dual_payload() [api/providers/aggregate.py]
                │    ├─> jolpica_provider.export_payload()
                │    └─> fastf1_provider.export_payload()
                │    └─> _merge_payloads() (wenn beide erfolgreich)
                ├─> build_output_name() (Circuit-basiert)
                ├─> unique_path() (Kollisionsvermeidung)
                └─> JSON schreiben
```

### Pfad C: GUI-Export ("All Sessions")
```
GUI: Session-Picker → "All Sessions"
 └─> expand_session_group("All Sessions")
      → ["FP1", "FP2", "FP3", "Q1", "Q2", "Q3", "SQ", "SS", "SR", "R"]
 
[Für jede Session in Liste:]
 └─> run_export(season, round, session, outdir)
      └─> (siehe Pfad B: build_dual_payload → JSON)
```

---

## 5. Ressourcen-Ladepfade

### PyInstaller-kompatible Ressourcen
**Funktion:** `api/export_service.py → resource_path()`
```python
def resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return (base / rel).resolve()
```

**Verwendung:**
```python
circuits_json = load_json("mapping/circuits.json")
# → Lädt entweder aus:
#    - sys._MEIPASS/mapping/circuits.json (EXE)
#    - project_root/mapping/circuits.json (Dev)
```

**Geladene Ressourcen:**
- `mapping/circuits.json`
- `mapping/drivers.json`
- `mapping/teams.f1.json`
- `mapping/lineups.f1.json`
- `mapping/nations.json`
- `mapping/championships.json`
- `mapping/cars.f1.json`
- `config.json`

---

## 6. External API Entry-Points

### Jolpica F1 API
**Base URL:** `http://api.jolpi.ca/ergast/f1`

**Endpoints:**
- `GET /{year}.json` - Season-Kalender
- `GET /{year}/{round}/qualifying.json` - Qualifying-Results
- `GET /{year}/{round}/results.json` - Race-Results
- `GET /{year}/{round}/sprint.json` - Sprint-Results (wenn verfügbar)

**Provider:** `api/providers/jolpica_provider.py`

### FastF1 API
**Library:** `fastf1>=3.6.0`

**Entry-Point:**
```python
import fastf1
session = fastf1.get_session(year, round_no, session_identifier)
session.load()
```

**Provider:** `api/providers/fastf1_provider.py`

**Cache:** Automatisches Disk-Caching in `~/.fastf1/cache/`

---

## Zusammenfassung

### Start-Optionen
1. **CLI:** `python main.py --season 2024 --round 5 --session Q`
2. **GUI:** `python gui_app.py` oder `LooneyF1Tool.exe`
3. **Tests:** `pytest tests/`

### Haupt-Orchestrierung
- **Legacy CLI:** `main.py → export_session()`
- **Modern GUI:** `gui_app.py → run_export()`
- **Export-Engine:** `api/export_service.py → run_export()`

### Daten-Fluss
```
User Input → Export-Engine → Provider-Router → [Jolpica | FastF1] → Aggregator → JSON-Export
```

### Kritische Abhängigkeiten
- `fastf1` - Backup-Datenquelle
- `requests` - Jolpica API-Calls
- `pandas` - DataFrame-Operationen
- `tkinter` - GUI (Standard-Library)

**Nächste Schritte:** Claims-Traceability, Provider-Fallback-Tests, Export-Format-Validierung
