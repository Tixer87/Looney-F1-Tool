**Release Date:** 6. November 2025
**Status:** Pre-release (Beta)
**Tag:** `v1.7.2_beta`
**Ziel:** RLT-ready JSON Exporte inkl. Qualifying-Split, Full-Event-Export, Validatoren.

---

## 🎯 Major Features

### 1) Qualifying Split Export (Q1/Q2/Q3)

* Lädt **eine** FastF1-Session `Q` und erzeugt **drei** Dateien: `..._Q1.json`, `..._Q2.json`, `..._Q3.json`.
* Segmentlogik:

  * **Q1:** alle Fahrer mit Q1-Zeit
  * **Q2:** Top-15 mit Q2-Zeit
  * **Q3:** Top-10 mit Q3-Zeit
* Pro Datei nur **Segmentzeit** (keine „Best of all“-Zeit).
* Sortierung aufsteigend nach Zeit; Zeitwerte als **Integer ms**.
* RLT-Felder: `Session="Q1|Q2|Q3"`, `TrackName`, `TrackUniqueName`, saubere Driver/Team-Mappings.

### 2) Full Event Export (Orchestrator)

* Ein Lauf exportiert **FP1, FP2, FP3, Q1–Q3,** optional **Sprint**, **Race**.
* Fehlende Sessions (kein Sprint-WE etc.) werden robust übersprungen und geloggt.

### 3) Validation & Tests

* `tools/validate_official_results.py` – vergleicht Exporte mit offiziellen Resultaten (Top-3, Pole, Winner, Counts).
* `tools/check_quali_exports.py` – Sanity-Check (ms-Typ, Sortierung, Segment-Counts).
* `tests/*` – Pytest-Abdeckung für Splitting & Dateien.

### 4) Year-Based Provider Routing

* Automatische Provider-Wahl nach Saisonjahr:

  * **≥ 2023:** FastF1
  * **≤ 2022:** Jolpica (Fallback für Historie)
* Transparenter Export ohne manuelle Umschaltung.

### 5) Mapping & Circuit Aliases

* Circuit-Auflösung gemäß `circuits.json`: `TrackName` = `CircuitName`, `TrackUniqueName` = `UniqueName`.
* Zusätzliche Aliase (Akzent/Schreibweise): Montréal/Montreal, São Paulo/Interlagos, Mexico/Mexico City, Budapest/Hungaroring, Marina Bay/Singapore, Lusail/Losail, Yas Island/Yas Marina u. a.
* Teams sauber getrennt: **Red Bull Racing** ≠ **Racing Bulls (RB/VCARB)**.

---

## 🔧 Technical Improvements

* **Deep-copy Fix** beim Segment-Split (keine Payload-Übernahme zwischen Q1/Q2/Q3).
* **Type Hints** und klare Konverter `_to_ms()` für stabile ms-Werte.
* **Dateinamen** konsistent: `YYYY_<TrackName>_<Session>.json`.
* **GUI-Titel** zeigt jetzt korrekt `v1.7.2_beta`.

---

## 📊 Performance

* Exportdauer Australien (komplett): wenige Sekunden je Session inkl. Q-Split.
* Lean JSONs (Q3 meist am kleinsten, da Top-10).

---

## ✅ Validation Status (Australia 2025 – R1, Melbourne)

* FP1–FP3: je 20 Fahrer
* Q1 (19), Q2 (15), Q3 (10) – **Pole: Norris #4**
* Race: **Winner: Norris #4**
* RLT-Compliance: 3/3 Quali-Files ok
* Pytest: grün

---

## 🐞 Known Issues

1. **Sprint-Varianten**: Export nur, wenn Wochenende Sprint enthält; einzelne Events erfordern ggf. Alias-Nachpflege.
2. **Misch-Saisons**: Nutzung 2024-Daten mit 2025-Lineup erzeugt Warnungen (Design-bedingt, Export ok).

---

## 📦 Dateien (relevant)

* `core/export_event.py` – Orchestrator (All Sessions)
* `export/qualifying_exporter.py` – Q → Q1/Q2/Q3
* `tools/validate_official_results.py`, `tools/check_quali_exports.py`, `tools/export_batch.py`
* `api/providers/*` – Provider & Routing
* `mapping/*` – Aliase/Mappings (Teams, Circuits)

---

## 🚀 Verwendung

1. Release-ZIP laden, entpacken, `LooneyF1Tool.exe` starten.
2. **All Sessions** wählen → FP/Quali-Split/Race landen im Exportordner.
3. Validator ausführen (`tools/validate_official_results.py`) und anschließend RLT-Import (Q1/Q2/Q3 + Race).

---

**Version:** 1.7.2_beta • **Tag:** `v1.7.2_beta` • **Status:** Beta

---
