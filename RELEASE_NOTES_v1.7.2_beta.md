**Release date:** 6 Nov 2025
**Status:** Pre-release (Beta)
**Tag:** `v1.7.2_beta`

---

## ✨ Highlights

### 🏁 Qualifying Split Export (Q1 / Q2 / Q3)

* Loads **one** FastF1 `Q` session and writes **three** JSON files: `..._Q1.json`, `..._Q2.json`, `..._Q3.json`.
* Knockout logic:

  * **Q1:** all drivers with Q1 time
  * **Q2:** top 15 with Q2 time
  * **Q3:** top 10 with Q3 time
* Each file contains **segment times only** (no cross-segment best).
* Sorted by time ascending; times stored as **integer milliseconds**.
* RLT-ready layout: `Session = Q1|Q2|Q3`, correct `TrackName`/`TrackUniqueName`, clean driver/team mapping.

### 🚀 Full Event Export (One-click)

Exports **FP1, FP2, FP3, Q1–Q3,** optional **Sprint**, and **Race** in one go.
Missing sessions (e.g., no sprint weekend) are skipped gracefully with clear logs.

### 🧪 Validation & Tests

* `tools/validate_official_results.py` – checks exports vs official results (Top-3, Pole, Winner, counts).
* `tools/check_quali_exports.py` – sanity checks (ms type, sorting, segment counts).
* `tests/*` – pytest coverage for splitting and file outputs.

### 📅 Year-based Provider Routing

* **≥ 2023:** FastF1
* **≤ 2022:** Jolpica (historical fallback)
  Zero manual switching needed.

### 🗺️ Circuit & Mapping Improvements

* Circuit mapping: `TrackName = CircuitName`, `TrackUniqueName = UniqueName` (from `circuits.json`).
* Extra aliases (accents/spellings): Montréal/Montreal, São Paulo/Interlagos, Mexico/Mexico City, Budapest/Hungaroring, Marina Bay/Singapore, Lusail/Losail, Yas Island/Yas Marina, etc.
* Team mapping clarified: **Red Bull Racing** ≠ **Racing Bulls (RB / VCARB)**.

---

## 🔧 Technical Improvements

* Deep-copy fix during Q split (no payload bleed between Q1/Q2/Q3).
* Type hints and stable `_to_ms()` conversions (always int ms).
* Consistent filenames: `YYYY_<TrackName>_<Session>.json`.
* GUI now shows **v1.7.2_beta**.

---

## ⚡ Performance

* Australia full export completes in a few seconds per session (including Q split).
* Lean JSON sizes (Q3 typically smallest due to top-10 only).

---

## ✅ Validation (Australia 2025 – Round 1, Melbourne)

* FP1–FP3: 20 drivers each
* Q1 (19), Q2 (15), Q3 (10) — **Pole: Lando Norris #4**
* Race — **Winner: Lando Norris #4**
* RLT compliance: ✅ all 3 quali files
* Pytest: ✅ all tests green

---

## 🐞 Known Issues

1. **Sprint variants:** Export only created when the weekend actually has sprint sessions (some events may need an extra alias).
2. **Mixed seasons:** Using 2024 data with a 2025 lineup yields warnings (by design); exports are still valid.

---

## 🗂️ Key Files & Modules

* `core/export_event.py` — one-click “All Sessions” orchestrator
* `export/qualifying_exporter.py` — Q → Q1/Q2/Q3 splitter
* `tools/validate_official_results.py`, `tools/check_quali_exports.py`, `tools/export_batch.py`
* `api/providers/*` — provider routing
* `mapping/*` — teams/circuits aliases

---

## 📥 Installation & Usage

1. Download the ZIP from this release.
2. Extract and run `LooneyF1Tool.exe`.
3. Pick **Season** and **Round**, click **All Sessions**.
4. Import into RLT: use the three quali files (Q1/Q2/Q3) + Race separately.

**Checksum (ZIP):**

```
F804C8D0ABFE1EC947D87B585D2F148637B71C45186107E9B4F87D2A0C4D91E0
```

---

