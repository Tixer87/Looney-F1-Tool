# Looney F1 Tool

Looney F1 Tool is an open source Windows tool for retrieving real Formula racing results and exporting them into the native Racing League Tools format.

Current version: **1.9.1**

## Features

- Practice, Qualifying, Sprint Qualifying, Sprint and Race support
- FastF1 and Jolpica as primary data sources
- OpenF1 as technical fallback
- Native Racing League Tools export
- Driver positions, numbers, teams, laps, gaps, times and points
- DNF, DNS and DSQ handling
- Automated validation and regression tests
- Optional live recorder
- Windows EXE build support

## Racing League Tools

Looney F1 Tool exports directly into the native RLT structure.

Validated workflow:

```text
Looney export
→ RLT import
→ Add result to season
→ Generate result graphic
```

Tested with **Racing League Tools 0.9.8 Hotfix 1**.

## Install

Python 3.11 is recommended.

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the GUI:

```powershell
python gui_app.py
```

Start the CLI:

```powershell
python main.py
```

Run tests:

```powershell
python -m pytest
```

Build the Windows EXE:

```powershell
.\Build.ps1
```

## Project structure

```text
api/             Data providers and API handling
core/            Session and result processing
export/          Racing League Tools export
live_recorder/   Live session recorder
mapping/         Drivers, teams, circuits and aliases
tests/           Automated tests
tools/           Validation and helper tools
utils/           Shared utilities
docs/            Documentation
```

## Validation

Version 1.9.1:

```text
129 passed
5 skipped
0 failed
134 total
```

The test suite covers export generation, provider fallback behavior, mappings, schemas, native RLT output, live recording and regression cases.

## Data sources

Looney F1 Tool uses:

- FastF1
- Jolpica
- OpenF1

Missing result data is not intentionally invented or reconstructed.

## Disclaimer

Looney F1 Tool is an independent GridSync community project and is not affiliated with Formula 1, FIA, Formula One Management, Racing League Tools, FastF1, Jolpica or OpenF1.

All trademarks and names belong to their respective owners.

## License

MIT License. See `LICENSE`.

---

www.gridSync.ch / Tixer87
