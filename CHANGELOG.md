# Changelog

All notable changes to the Looney F1 Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.9.1] - 2026-10-01

### Changed

- Major codebase cleanup and simplification
- Reduced local mapping data to project owned alias maps and fallback calendar data
- Consolidated duplicate Jolpica API implementations into `api/jolpica_api.py`
- Removed obsolete provider aggregation layer
- Removed unused cache and duplicate version modules
- Removed legacy validation tools tied to outdated export formats
- Simplified CLI, GUI, provider, export, live recorder and utility modules
- Removed obsolete comments, docstrings, dead imports, dead functions and redundant fallback paths
- Removed old Formula Toons branding, legacy banners and outdated CLI text
- Centralized version information in `core/version.py`
- Updated application version to `1.9.1`
- Updated Windows build output to `LooneyF1Tool_1.9.1.exe`
- Added `config.json` explicitly to the PyInstaller build
- Updated default configuration for the current provider architecture

### Data and Mapping Cleanup

Removed obsolete mapping files:

- `native_teams.json`
- `circuits.json`
- `drivers.json`
- `teams.f1.json`
- `lineups.f1.json`
- `nations.json`
- `cars.f1.json`
- `championships.json`

Retained project mapping data:

- `driver_alias_map.json`
- `team_alias_map.json`
- `nations_alias_map.json`
- `fallback_calendars.json`

Circuit, driver, team and nationality lookup logic now relies on project maintained mappings and provider supplied data instead of bundled RLT reference data.

### Export

- Native RLT export remains the primary output path
- Native circuit metadata now uses the internal circuit mapping
- Driver nationality and team information comes from provider payloads and project mappings
- Preserved race gaps, lap gaps, classifications, points, qualifying phases and status handling
- Preserved native RLT and legacy RLT validation support
- Removed obsolete export helper logic and redundant imports

### Providers

- FastF1 remains the primary provider for modern seasons
- Jolpica remains available as a structured results provider
- OpenF1 remains the technical fallback for supported seasons
- Consolidated Jolpica networking, health check, schedule and result handling
- Removed unused `aggregate.py`
- Removed duplicate `api/providers/jolpica_api.py`

### Live Recorder

- Simplified client, processor, recorder, exporter and state modules
- Simplified lap, pitstop and race control detectors
- Removed comments, docstrings and redundant helper code
- Preserved native RLT live export support
- Preserved lap, pitstop, SC, VSC, red flag and weather tracking

### CLI and GUI

- Rebuilt `main.py` around the current export architecture
- Reduced legacy CLI code substantially while preserving export functionality
- Removed obsolete live recorder CLI path using retired classes
- Removed Formula Toons and cartoon themed output
- Simplified grouped session export handling
- Simplified GUI calendar and export workflow
- Removed unused GUI dialogs and placeholder log filtering code
- Removed redundant GUI export helper methods

### Build and Repository

- Python 3.11 remains the build target
- Build uses `uv`, locked dependencies and PyInstaller
- Removed temporary repository audit files
- Removed stale repository structure snapshot
- Expanded `.gitignore` for test temp output
- Cleaned root configuration and build files
- Updated README for version `1.9.1`

### Testing

Current test suite:

```text
129 passed
5 skipped
0 failed
134 total
```

The suite covers providers, mappings, schemas, native RLT export, regression cases, live recording and version consistency.

---

## [1.8.0] - 2025-11-23

### Added

- Live recording via f1-dash integration
- New `live_recorder` subsystem
- Lap, pitstop, race control and weather tracking
- RLT compatible live session export

### Fixed

- Team mapping for live data
- Driver and nationality handling
- DNF handling
- Pitstop detection for mid session starts
- Race control parsing
- Python datetime compatibility

### Documentation

- Added live recorder implementation documentation
- Added f1-dash specification and validation material

---

## [1.7.2_beta] - 2025-11-06

### Added

- Qualifying export with Q1, Q2 and Q3 splitting
- Full event export
- Batch export tool
- Export validation tooling

### Fixed

- FastF1 qualifying filtering
- Version display
- Qualifying driver selection

### Technical

- Centralized version handling
- Added version validation tests
- Retained provider fallback architecture

---

## [1.7.1] - 2025-11-02

### Fixed

- RLT import structure
- Driver `InGameName`
- Race type handling
- Status mapping
- Seat type handling

### Added

- Jolpica provider health check
- Provider router
- Pytest coverage for providers and RLT adapter contracts

### Technical

- Unified provider to adapter export path

---

## [1.7.0] - 2025-11-01

### Added

- Initial modernization release
- English GUI
- Logging system
- Interactive calendar
- Provider architecture
- Circuit based filenames
- Sprint detection

### Changed

- Modernized export engine
- Improved provider fallback handling

### Technical

- FastF1 integration
- Provider pattern
- Export service with collision safe filenames
