# Looney F1 Tool 1.6 - Vollständiges Inventar

**Erstellungsdatum:** 01.11.2025  
**Audit-Basis:** Read-Only Analyse des Projektverzeichnisses

---

## Projektstruktur (Überblick)

```
Looney F1 Tool 1.6/
├── api/                    # API-Schicht (Datenquellen & Export)
├── core/                   # Business Logic (Session-Building, Driver-Blocks)
├── export/                 # Export-Engine (RLT JSON)
├── mapping/                # Statische Mapping-Dateien (Teams, Drivers, Circuits, etc.)
├── utils/                  # Hilfsfunktionen (Config, Caching, Rate-Limiting)
├── tests/                  # Test-Suite (Unit-Tests, Smoke-Tests)
├── tools/                  # Zusatz-Werkzeuge (falls vorhanden)
├── docs/                   # Dokumentation
├── audit/                  # Audit-Ergebnisse (dieser Bericht)
├── build/                  # PyInstaller Build-Artefakte
├── dist/                   # Compiled Distribution
├── .venv/                  # Python Virtual Environment
├── _internal/              # PyInstaller Runtime-Dateien (legacy?)
├── LooneyF1Tool_1.6_Win64_portable/  # Portable Distribution-Paket
├── rlt-ready/              # Standard Export-Zielordner
├── main.py                 # CLI Entry-Point
├── gui_app.py              # GUI Entry-Point (tkinter)
├── config.json             # Hauptkonfiguration
├── requirements.txt        # Python Dependencies
├── LooneyF1Tool.spec       # PyInstaller Build-Spec
├── LooneyF1Tool.iss        # Inno Setup Script (Installer)
├── LooneyF1Tool.exe        # Kompilierte Anwendung
└── README.md               # Hauptdokumentation
```

---

## Detaillierte Dateibeschreibungen

### Haupt-Entry-Points

#### `main.py` (289 Zeilen)
**Zweck:** Command-Line Interface für Export-Operationen  
**Hauptfunktionen:**
- `export_session()` - Orchestriert Export für spezifische Session (Round, Endpoint)
- `list_races()` - Abrufen der Rennkalender via Jolpica API
- `print_welcome_banner()` - ASCII-Banner mit Rich-Library oder Fallback
- CLI-Argument-Parsing mit `argparse`

**Dependencies:** 
- `api.jolpica_api` (Legacy-Import)
- `core.session_builder`, `core.driver_block`
- `export.rlt_exporter`
- `utils.config_loader`

#### `gui_app.py` (668 Zeilen)
**Zweck:** Grafisches Benutzerinterface (tkinter-basiert)  
**Hauptkomponenten:**
- `CalendarWindow` - Interaktiver Kalender mit Doppelklick/Rechtsklick-Menü
- `LogView` - Color-coded Logging-Widget
- Main GUI - Session-Auswahl, Export-Steuerung, Multi-Threading

**Features:**
- 4-Spalten Kalender: Round | Date | Grand Prix | Circuit
- Datum im Format DD.MM.YYYY
- "All Sessions" Bulk-Export
- Threading für UI-Reaktivität während Export

---

### API-Schicht (`api/`)

#### `api/jolpica_api.py`
**Legacy-Modul:** Direkte Jolpica API-Aufrufe (ursprüngliche Implementierung)  
**Status:** Teilweise deprecated, ersetzt durch Provider-Pattern

#### `api/export_service.py` (ca. 200 Zeilen)
**Hauptmodul:** Modernisierte Export-Orchestrierung  
**Key Functions:**
- `run_export()` - Haupt-Export-Funktion mit Dual-Source Aggregation
- `build_output_name()` - Circuit-basiertes Filename-Schema
- `unique_path()` - Kollisionsvermeidung
- `expand_session_group()` - Mapping von Session-Gruppen zu individuellen Sessions
- `resource_path()` - PyInstaller-kompatible Ressourcen-Pfade

**Features:**
- Unterstützt erweiterte Session-Codes (FP1-3, Q1-3, SQ/SS/SR, R)
- Circuit-Namen statt "roundX" in Dateinamen
- Automatische Fallback-Chain (Jolpica → FastF1)

#### `api/data_mapper.py`
**Zweck:** Mapping von API-Rohdaten auf RLT-Format  
**Funktionen:** Name-Resolving, Team-Zuordnung, Circuit-Lookup

#### `api/providers/` (Provider-Pattern)

**`base.py`**
- `DataProvider` Protocol
- `SessionType` Type Definitions

**`jolpica_provider.py`**
- Implementierung des Jolpica-Providers
- `schedule()`, `export_payload()` Funktionen

**`fastf1_provider.py`**
- FastF1 v3.6.1 Integration
- Sprint-Code-Varianten: SQ → SS → S Fallback
- Cache-Management

**`router.py`**
- Fallback-Logik: `schedule_with_fallback()`, `export_payload_with_fallback()`
- Primary: Jolpica, Secondary: FastF1

**`aggregate.py`**
- **Dual-Source Aggregation**
- `build_dual_payload()` - Intelligente Datenverschmelzung
- `_merge_payloads()` - Lücken aus sekundärer Quelle füllen
- `get_source_status()` - Diagnostics

---

### Core-Logik (`core/`)

#### `core/session_builder.py`
**Zweck:** Erstellt Session-Metadata (Track, SessionType, Round, etc.)  
**Output:** Session-Dictionary für RLT-Export

#### `core/driver_block.py`
**Zweck:** Baut Driver-Arrays mit allen Timing-Daten  
**Datenquellen:** Qualifikationszeiten, Race-Results, Positionen, Gaps

#### `core/helpers.py`
**Zweck:** Hilfsfunktionen für Core-Logic  
**Funktionen:** Zeit-Formatierung, Position-Normalisierung, etc.

---

### Export-Engine (`export/`)

#### `export/rlt_exporter.py`
**Zweck:** Finaler JSON-Export im Racing League Tools Format  
**Funktionen:**
- `export_rlt_json()` - Schreibt strukturierte JSON-Datei
- Validierung der Pflichtfelder
- Pretty-Print mit Indentation

---

### Mapping-Dateien (`mapping/`)

**Statische JSON-Ressourcen:**

- `circuits.json` - Circuit-Namen, Locations, TrackUniqueName
- `drivers.json` - Fahrer-Database (Name, Number, Nationality)
- `teams.f1.json` - Team-Informationen
- `lineups.f1.json` - Saison-Lineups
- `nations.json` - Country-Codes & Flaggen
- `championships.json` - Championship-Metadata
- `cars.f1.json` - Fahrzeug-Daten

**Verwendung:** Werden via `resource_path()` geladen (PyInstaller-kompatibel)

---

### Utilities (`utils/`)

#### `utils/config_loader.py`
**Zweck:** Lädt `config.json` für Default-Werte  
**Functions:** `get_default_year()`, `get_default_export_dir()`

#### `utils/caching.py`
**Zweck:** Cache-Management (vermutlich für FastF1)  
**Features:** Disk-Cache für Telemetrie-Daten

#### `utils/rate_limit.py`
**Zweck:** Rate-Limiting für API-Aufrufe  
**Implementierung:** Decorator oder Throttle-Mechanismus

---

### Test-Suite (`tests/`)

#### `tests/test_export_smoke.py`
**Zweck:** Smoke-Tests für Export-Pipeline  
**Coverage:** Basic Happy-Path Tests

#### `tests/test_resources_exist.py`
**Zweck:** Validierung der Mapping-Ressourcen  
**Prüfung:** Existenz aller JSON-Dateien

#### `tests/unit/`
**Zweck:** Unit-Tests für Module  
**Status:** (Zu prüfen, ob vollständig)

---

### Build & Distribution

#### `LooneyF1Tool.spec` (PyInstaller)
**Konfiguration:**
- Entry-Point: `gui_app.py`
- Datas: `mapping/`, `config.json`
- Hidden-Imports: `fastf1.events`, `fastf1.api`, `fastf1.core`, `pandas`
- Output: `--onedir` (Directory-Bundle)
- Console: `False` (Windowed)
- UPX: `True` (Kompression)

#### `LooneyF1Tool.iss` (Inno Setup)
**Zweck:** Windows-Installer-Erstellung  
**Output:** Setup-Wizard für Installation

#### `LooneyF1Tool.exe` (ca. 29 MB)
**Status:** Vorgefundene EXE im Projektstamm  
**Hash (SHA256):** `073E6DC68BA705576FB0AA87F61B1FFE96A16C83EABD5FCFF99480D7E3AD2FFF`  
**Last Modified:** 14.09.2025 16:23:12  
**Größe:** 30.539.483 Bytes (~29 MB)

#### `dist/` & `build/`
**Zweck:** PyInstaller Build-Artefakte  
**Inhalt:** 
- `dist/LooneyF1Tool/` - Komplettes Anwendungsbundle mit `_internal/`
- `build/` - Temporäre Build-Dateien

#### `LooneyF1Tool_1.6_Win64_portable/`
**Zweck:** Fertig paketierte Portable-Distribution  
**Inhalt:** EXE + `_internal/` + Dokumentation

#### `_internal/` (im Projektstamm)
**Status:** Legacy-Ordner, möglicherweise von alter Build-Struktur  
**Hinweis:** Moderne PyInstaller-Versionen legen `_internal/` in `dist/` ab

---

### Konfiguration & Dokumentation

#### `config.json`
**Inhalt:**
```json
{
  "year": 2024,
  "round": 1,
  "api_base_url": "http://api.jolpi.ca/ergast/f1",
  "default_year": 2024,
  "default_export_dir": "rlt-ready"
}
```

#### `requirements.txt`
**Python-Abhängigkeiten:**
- Core: `requests`, `pandas`, `numpy`, `fastf1>=3.6.0`
- GUI: `rich`, `flask-socketio` (optional)
- Build: `pyinstaller>=6.10.0`
- Testing: `pytest`

**Installierte Pakete (freeze):** Siehe `audit/looney_audit/env/requirements.freeze.txt` (128 Pakete)

#### Dokumentations-Dateien
- `README.md` - Hauptdokumentation (User-facing)
- `README_Modernization.md` - v1.6 Feature-Changelog
- `RELEASE_NOTES.md` - Community Release Notes
- `validation_checklist_2025.md` - 2025-Season Verification
- `BEREINIGUNGSLISTE_COMMUNITY.md` - Cleanup-Liste
- `LICENSE` - MIT-Lizenz

---

## Besondere Verzeichnisse

### `rlt-ready/`
**Zweck:** Standard-Zielordner für Exporte  
**Konfigurierbar:** via `config.json` oder GUI-Auswahl

### `circuits/`, `images/` (wenn vorhanden)
**Zweck:** Zusätzliche Assets für UI oder Export  
**Status:** Im Workspace-Kontext nicht direkt sichtbar (evtl. in Tool/-Ordner)

---

## Python-Umgebung

**Python-Version:** 3.13.1  
**Virtuelle Umgebung:** `.venv/` vorhanden  
**Paket-Manager:** pip  
**Installierte Pakete:** 128 (siehe freeze)

**Besondere Dependencies:**
- `fastf1==3.6.1` (oder neuer aus freeze)
- `pandas==2.3.0`, `numpy==2.3.1`
- `pyinstaller==6.16.0`
- `pytest==8.4.2`
- `rich==14.0.0`

---

## Build-Artefakte (gefunden)

1. **`LooneyF1Tool.exe`** (Projektstamm)
   - 29 MB, erstellt 14.09.2025
   - SHA256: `073E6DC68BA705576FB0AA87F61B1FFE96A16C83EABD5FCFF99480D7E3AD2FFF`

2. **`dist/LooneyF1Tool/`** (falls vorhanden)
   - Vollständiges PyInstaller-Bundle
   - `LooneyF1Tool.exe` + `_internal/` Ordner

3. **Portable Package:** `LooneyF1Tool_1.6_Win64_portable/`

---

## Nicht erfasste/fehlende Komponenten

- **Web-Interface:** Bewusst entfernt (laut RELEASE_NOTES.md)
- **Live-Telemetrie:** Nicht in Community-Version enthalten
- **UDP-Dumper:** Ordner `udp_dumper/` vorhanden (nicht näher untersucht)
- **Werkzeuge:** `tools/` Ordner vorhanden (Inhalt nicht detailliert)

---

## Zusammenfassung

- **Codebase:** ~2000+ Zeilen Python (geschätzt, ohne Tests/Libs)
- **Module:** 15+ Python-Dateien (ohne Tests)
- **Ressourcen:** 7 JSON-Mapping-Dateien
- **Tests:** Vorhanden, Coverage unbekannt
- **Build:** PyInstaller + Inno Setup
- **Distribution:** Standalone EXE (Windows)

**Nächste Schritte:** Entry-Point-Analyse, Claims-Traceability, Code-Walkthrough
