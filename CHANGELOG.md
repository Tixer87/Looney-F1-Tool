# Changelog

All notable changes to the Looney F1 Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.8.0] - 2025-11-23

### ✨ Added - Live Recording via f1-dash Integration

- **New `live_recorder` subsystem** for real-time F1 session recording
  - Connects to [f1-dash](https://github.com/Tixer87/f1-dash) SSE service and records live sessions
  - Detects laps, pitstops, race control events (SC/VSC/Red Flag) and weather updates
  - Exports fully Racing League Tools (RLT) compatible JSON at session end
  - **100% test coverage** (6/6 tests passing, 0 warnings, Python 3.12 compatible)

### Technical Implementation

- **New module tree**:
  - `live_recorder/state.py` – Session and driver state data classes
  - `live_recorder/processor.py` – Event processing pipeline with case-insensitive parsing
  - `live_recorder/recorder.py` – SSE orchestration and recording lifecycle
  - `live_recorder/exporter.py` – RLT JSON exporter for live sessions
  - `live_recorder/detectors/` – Lap, pitstop and race control detectors
  - `live_recorder/client.py` – SSE client wrapper

- **CLI integration**:
  - New `--backend f1dash_live` option
  - New `--mode record` option for live recording
  - New `--f1dash-url` option (default: http://localhost:4000)
  - New `--output-dir` option for live recordings

### 🐛 Fixed

- Team name mapping for f1-dash data (Red Bull Racing → Red Bull, Visa Cash App RB → Racing Bulls, etc.)
- Nation mapping using direct `countryCode` from f1-dash
- Driver name extraction using `fullName` field
- Case-sensitivity handling for f1-dash events (CamelCase + lowercase fallback)
- DNF handling in lap detection (retired/stopped drivers skipped)
- Pitstop detection for mid-session starts (stint count initialization)
- Race control parsing with auto-category detection
- Python 3.12 compatibility (replaced deprecated `datetime.utcnow()`)

### 📚 Documentation

- Added comprehensive technical documentation (`docs/LIVE_RECORDER_IMPLEMENTATION.md`)
- Moved F1 DASH specification to `docs/` directory
- Validation report moved to `docs/` directory

### Usage

Start f1-dash locally, then run:
```bash
python main.py --backend f1dash_live --mode record --f1dash-url http://localhost:4000 --output-dir ./output/live
```

After the session finishes, a ready-to-import RLT JSON export is written to the output directory.

---

## [1.7.2_beta] - 2025-11-06

### ✨ New Features
- **Qualifying Export Fixed**: Q-Session automatically splits into Q1/Q2/Q3 files
  - Correct filtering by participation (19/15/10 drivers)
  - Sorting by respective Q-session time
  - Validated against official 2025 Melbourne results
- **Full Event Export** (`core/export_event.py`)
  - Export all sessions of an event at once (FP1/FP2/FP3, Q1/Q2/Q3, Sprint, Race)
  - Automatic error handling for missing sessions
- **Official Results Validator** (`tools/validate_official_results.py`)
  - Validate exports against official data (driver counts, Top 3, Winner, Pole)
- **Qualifying Export Checker** (`tools/check_quali_exports.py`)
  - RLT compliance verification, team mapping validation, time format checks
- **Batch Export Tool** (`tools/export_batch.py`)
  - Export multiple rounds: `python tools/export_batch.py 2025 1 5`

### 🐛 Bug Fixes
- Version display: GUI now shows "v1.7.2_beta" (was "v1.6")
- FastF1 Q-Session: Time-based filtering instead of GridPosition
- Qualifying driver filtering moved before `_build_driver()` to preserve Q1/Q2/Q3 fields

### 🧪 Testing
- Added pytest integration (`tests/test_event_australia_paths.py`)
- 4 automated tests for export quality
- Australia 2025 R1 fully validated ✅

### 📦 Build Information
- Size: 195.2 MB (uncompressed), 87.9 MB (zipped)
- Files: 2138 | Platform: Windows 64-bit | Python: 3.13.1
- SHA256: `DC8FDF2E76E72154EDB8DDA4A5DC3FECB4718EE858867F29DFFF7E3C9C2DAF8A`

### ✅ Verified Events
- **Australia 2025 R1**: FP1/FP2/FP3 (20), Q1 (19), Q2 (15), Q3 (10), Race (20, Winner: Norris #4)

### Technical
- Centralized version system across app/GUI/CLI/build artifacts
- Windows file metadata (FileVersion/ProductVersion) set to 1.7.2.0
- `core/version.py`: Single source of truth for version
- RLT export format fixes retained from 1.7.1
- Router fallback (Jolpica→FastF1) remains active
- `tests/test_version.py`: Version validation tests

## [1.7.1] - 2025-11-02

### Fixed
- **RLT import format**: Match working file format exactly
  - Removed Session wrapper - use top-level fields directly
  - Use Driver.InGameName instead of Driver.Nationality
  - Removed extra fields not in working files (NationalityIngame, Car, StintsRaw, FastestLapTyres)
  - Changed RaceType default from 'Regular' to 'Main'
  - Map Status 'Finished' to 'Ok' in FastF1 adapter path
  - Set SeatType to 'Primary' string (not null)
  - Maintain exact field order matching working RLT files

### Added
- **Jolpica provider with health-check**
  - HTTP client with retry/backoff (3x), timeouts
  - Refactored to use only jolpica_api (no main imports)
  - Standardized session raw format for export_service

- **Provider router with fallback**
  - get_provider() with Jolpica-first, FastF1 fallback logic
  - FastF1ProviderWrapper wraps existing fastf1_provider functions
  - Health-check determines provider availability

- **Tests (pytest)**
  - test_jolpica_healthcheck.py: Health-check returns bool, retries on failure
  - test_provider_router.py: Jolpica preferred, fallback to FastF1, direct prefer
  - test_rlt_adapter_contract.py: No Session wrapper, InGameName, RaceType Main

### Technical
- Export service uses get_provider() instead of old dual-source
- Single path through router → provider → rlt_adapter
- Smoke test: 2025 Melbourne Race exports successfully (20 drivers, 15136 bytes)

## [1.7.0] - 2025-11-01

### Added
- Initial modernization release
- English UI interface
- Advanced logging system with color-coded levels
- Interactive calendar window with context menus
- Robust data provider system (Jolpica → FastF1 fallback)
- Circuit-based filename schema
- Sprint race detection

### Changed
- Complete GUI translation from German to English
- Modernized export engine with provider pattern
- Enhanced error resilience with automatic provider switching

### Technical
- FastF1 v3.6.1 integration with local caching
- Provider pattern implementation (base.py, jolpica_provider.py, fastf1_provider.py, router.py)
- New export service with safe naming and collision avoidance
