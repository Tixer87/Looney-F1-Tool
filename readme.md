# Looney F1 Tool — v1.7.2_beta

Turn real Formula 1 sessions from **Jolpica / FastF1** into **Racing League Tools–ready JSON**—fully mapped, cleanly structured, and exportable with one click.
This release introduces the **Qualifying split** (Q ➜ Q1/Q2/Q3) and a **Full Event Export** that saves you time and avoids manual stitching.

![Looney F1 v1.7.2\_beta](https://img.shields.io/badge/Looney%20F1-v1.7.2_beta-magenta?style=for-the-badge\&logo=formula1)

---

## What it does ✨

* **Qualifying split**: Loads a single “Q” session and outputs three separate JSON files for **Q1**, **Q2**, and **Q3**, matching Racing League Tools’ native import flow.
* **Full Event Export**: One action exports **FP1, FP2, FP3, Q1–Q3, Sprint (if present), and Race** into your chosen folder—no manual merges, no guesswork.
* **Trustworthy output**: Results are validated against official classifications with built-in tools, so what you export is what you expect.

---

## Why it’s useful 🏁

* **True-to-format Qualifying**: Each round (Q1/Q2/Q3) contains only its segment times and participants (Q1: all drivers with a Q1 time, Q2: top 15 with a Q2 time, Q3: top 10 with a Q3 time). This mirrors how qualifying is actually run—and how Racing League Tools expects data.
* **Consistent timing**: All lap and session times are stored as **integer milliseconds** for precision and easy downstream processing.
* **Reliable mapping**: Driver, team, nationality, and circuit names are normalized. Notably, **Red Bull Racing** and **Racing Bulls (RB / VCARB)** are treated as distinct teams to prevent confusion.
* **Zero manual editing**: Pick **Season** and **Round**, click **All Sessions**, and you’re done.

---

## What’s included in v1.7.2_beta 📦

* **Exporters**

  * Race, Practice (FP1–FP3), Qualifying Split (Q ➜ Q1/Q2/Q3), Sprint (where applicable).
* **Validation & QA**

  * Official results check (Top-3, Pole, Winner, driver counts).
  * Sanity checks for qualifying files (time type, sorting, segment counts).
  * Pytest-based tests covering the split and file presence.
* **Mappings**

  * Drivers, teams, nationalities, and circuits, including accent/spelling aliases (e.g., Montréal/Montreal, São Paulo/Interlagos, Mexico/Mexico City, Budapest/Hungaroring, Marina Bay/Singapore, Lusail/Losail, Yas Island/Yas Marina).
  * Circuit mapping uses: **TrackName = CircuitName** and **TrackUniqueName = UniqueName**.
* **Provider routing**

  * Seasons from 2023 onward use FastF1 by default.
  * Earlier seasons fall back to Jolpica for historical coverage.

---

## Supported sessions & outputs 📁

* **Practice**: FP1, FP2, FP3
* **Qualifying**: Q split into **Q1**, **Q2**, **Q3** (three files)
* **Sprint weekends**: Sprint sessions appear when the weekend actually includes them
* **Race**: Full classification with mapped fields

Files are named consistently per event, season, and session. Qualifying produces three separate JSONs (Q1/Q2/Q3) that import directly into Racing League Tools. Race exports are saved separately.

---

## Quick start 🚀

1. Download the latest release ZIP and extract it.
2. Launch the app (LooneyF1Tool.exe).
3. Select **Season** and **Round** and press **All Sessions**.
4. Import **Q1**, **Q2**, **Q3** and **Race** into Racing League Tools.

That’s it—no manual editing, no stitching of partial results.

---

## Data quality & validation ✅

* **Official checks** confirm key outcomes: Top-3, Pole Position, winner, and driver counts per session.
* **Sanity checks** ensure times are integer milliseconds, results are sorted correctly, and segment participation matches Q1/Q2/Q3 rules.
* **Australia 2025 (Round 1, Melbourne)** has been fully verified end-to-end:

  * Practice sessions: 20 drivers each
  * Qualifying: Q1 (19), Q2 (15), Q3 (10) with **Pole: Lando Norris #4**
  * Race: **Winner: Lando Norris #4**
  * Racing League Tools import: passed

---

## Requirements & compatibility 🧩

* **Platform**: Windows 64-bit
* **Data**: Jolpica / FastF1 sources
* **Season coverage**: Optimized for 2025; older seasons supported via provider routing
* **Output**: JSON compatible with **Racing League Tools**

---

## Notes & known limitations 🔎

* Sprint sessions are exported only for sprint weekends.
* Timing is always stored as **integer milliseconds**.
* Team and circuit mappings are centralized; if an event uses an unusual alias, it may require an alias update before export.

---

## Roadmap 🗺️

* Additional circuit aliases where needed (rare cases).
* Extended sprint handling coverage and UI hints.
* Minor GUI refinements around qualifying selection and status messages.

---

## Support & feedback 💬

Found an inconsistency or need an alias added? Open an issue with the event, session, and a short description of the mismatch.
If you use this tool in content or league operations, a quick mention or star helps others find it.

---

**Looney F1 Tool v1.7.2_beta** — fast, mapped, and Racing League Tools–ready. Enjoy the clean exports and have a great season.

Append this at the very end of your README:

---

## Support this project ☕

If this tool saves you time, you can **buy me a coffee**:

<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="ktixerx" data-color="#FFDD00" data-emoji="🍺"  data-font="Cookie" data-text="Buy me a beer" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>
