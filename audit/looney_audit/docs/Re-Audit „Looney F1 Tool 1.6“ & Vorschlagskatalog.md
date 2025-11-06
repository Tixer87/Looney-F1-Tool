# 📋 CLAUDE-PROMPT (nur Dokumentation): Re-Audit „Looney F1 Tool 1.6“ & Vorschlagskatalog

**Modell:** Claude Sonnet 4.5
**Arbeitsverzeichnis:** `C:\Users\ktixe\Documents\Formula Toons Results\Looney F1 Tool 1.6`
**Wichtig:** **Keinerlei Quellcode- oder Spec-Änderungen.** Nur lesen, bauen, ausführen, messen, **dokumentieren**. Verbesserungen ausschließlich **als Vorschläge** mit Text-Diffs (Entwürfe), nicht anwenden.

---

## Ziele

1. Den **aktuellen Stand** des Programms vollständig, nachvollziehbar und **belegbar** dokumentieren (Code-Struktur, Abhängigkeiten, Build/EXE, Laufzeitverhalten, Export).
2. Einen **priorisierten** Katalog an **Verbesserungsvorschlägen** erstellen (Stabilität, Fallbacks, UX/Export, Performance/IO, Packaging, Tests, Security) – **ohne Umsetzung**.
3. Eine **Release-Einschätzung** („salonfähig jetzt / nur unter Bedingungen / nein“) liefern – begründet, mit konkreten Mindestkriterien.

---

## Artefakt-Ablage (ausschließlich im Repo)

Lege **alle** Reports/Beweise **im Projekt** unter `.\audit\looney_audit\` ab:

```
.\audit\looney_audit\
  docs\
  env\
  static\
  security\
  runtime\
  exe\
  sbom\
  screens\
  samples\
  patch_drafts\
```

* **Nur** in diesen Ordner schreiben.
* **Keine** Codeänderungen in `api/`, `core/`, `export/`, `mapping/`, `utils/`, `tools/`, `gui_app.py`, `main.py`, `LooneyF1Tool.spec`, `LooneyF1Tool.iss`.
* **Keine** Konfigurationsänderungen, außer rein temporär/konfigurativer Lauf (ohne Commit) für Smoke-Tests.

---

## Phase A — Standaufnahme (beweisbar, read-only)

### A1) Inventar & Einstiege

* Erfasse Verzeichnisbaum, **Entry-Points** (`main.py`, `gui_app.py`), Build-Dateien (`LooneyF1Tool.spec`, `LooneyF1Tool.iss`), Ressourcenordner (`api`, `core`, `export`, `mapping`, `utils`, `tools`), Testordner (`tests`), Binärpfade (`dist`, `build`, `LooneyF1Tool_1.6_Win64_portable`), Artefakte (`rlt-ready`, `_internal`, `.venv`).
* **Ergebnis:**

  * `docs/inventory.md` (Struktur + Kurzbeschreibung je Ordner/Datei)
  * `docs/entrypoints.md` (Startpfade, Hauptfunktionen, CLI/GUI)

### A2) Projekt-Doku ↔ Code (Behauptungen abgleichen)

* Lies `README.md`, `README_Modernization.md`, `RELEASE_NOTES.md`, `validation_checklist_2025.md`, `BEREINIGUNGSLISTE_COMMUNITY.md`.
* Mappe **jede** dort behauptete Funktion auf **konkrete Code-Stellen** (Datei:Zeilen) und bewerte den Status: **erfüllt / teilweise / offen**.
* **Ergebnis:** `docs/claims_traceability.md` (Tabelle: „Aussage → Datei:Zeilen → Status → Evidenz/Kommentar“).

### A3) Abhängigkeiten & Umgebung (read-only)

* Python-Version, OS, `pip freeze` (keine Upgrades/Locks).
* **Ergebnis:** `env/env_report.md`, `env/requirements.freeze.txt`.

### A4) Statische Checks & Typen (read-only)

* Linter (z. B. ruff/flake8) + mypy **nur Reports** (kein Auto-Fix).
* **Ergebnis:** `static/lint_report.csv`, `static/mypy_report.txt`, Kurzfazit `static/summary.md` (Risikokategorien: Laufzeit-kritisch / Stil).

### A5) Security & Lizenzen (read-only)

* `pip-audit`, `bandit`, Lizenzliste.
* **Ergebnis:** `security/pip_audit.json`, `security/bandit.txt`, `security/licenses.csv`, `security/risk_summary.md` (nur Befunde, **keine** Fixes).

### A6) Build & EXE-Validierung (ohne Spec-Änderung)

* Vorhandene EXE: `LooneyF1Tool.exe` in Projektstamm → **Hash** & **Größe** dokumentieren.
* Repro-Build nur mit **vorhandener** Spec (`LooneyF1Tool.spec`) – **keine Änderungen** an Spec/Flags.
* `dist\` Inhalt vollständig auflisten.
* **Ergebnis:**

  * `exe/hash_old.txt` (falls EXE alt), `exe/size_check.txt`
  * `exe/build_log.txt`, `exe/hash_new.txt`, `exe/hash_compare.txt`
  * `exe/exe_inventory.md` (Dateiliste inkl. `_internal`)

### A7) Laufzeit-Smoke (GUI/CLI/Exporter)

* Starte EXE und ggf. CLI-Hilfe; erfasse **Screenshots**: `screens/gui_start.png`.
* Erzeuge **Beispiel-Export** (typische Session). Bewahre Output unter `samples/` auf; konsolidiere die Aufrufe in `runtime/smoke_log.txt`.
* **Provider-Fallback** „Jolpica ok“ vs. „Jolpica simulated fail → FastF1 übernimmt“ **ohne** Codeänderung (z. B. über bestehende Konfiguration/Netzwerkbedingungen); beide Pfade protokollieren.
* **Ergebnis:**

  * `runtime/smoke_log.txt`
  * `runtime/provider_fallback/jolpica_ok.log`
  * `runtime/provider_fallback/jolpica_fail_fastf1_ok.log`
  * `runtime/provider_fallback/comparison.md`
  * `samples/*`, `screens/*`

### A8) Exportformat & Mapping-Konsistenz

* Beschreibe Struktur der erzeugten Exportdateien: Pflichtfelder, leere Felder (= 0/""), **Sortierung** (z. B. Driver-Blocks nach Position), `TrackName`/`TrackUniqueName`-Mapping, Namen/Teams/Nationen.
* Checke **Dateinamensschema** (Sanitizing, Timestamp, Kollisionen) an realen Beispielen.
* **Ergebnis:**

  * `docs/export_format_report.md`
  * `docs/mapping_consistency.md`
  * `runtime/filename_checks.md`

### A9) Leistung & Robustheit (Messung)

* Zeitmessungen (Datenabruf, Export), einfache IO/Memory-Beobachtung, prototypische Fehlerbilder (Timeouts, Rate-Limits, Null-Felder).
* **Ergebnis:** `docs/perf_observations.md`, `docs/error_catalog.md`.

### A10) Release-Status (Ist)

* Nüchterne Bewertung: **„salonfähig“** / **„salonfähig nach Erfüllung von Mindestkriterien“** / **„nicht salonfähig“** – mit Begründung und harten Mindestanforderungen.
* **Ergebnis:** `docs/release_status_now.md`.

---

## Phase B — Verbesserungen **nur vorschlagen**, nicht umsetzen

### B1) Priorisierte Vorschläge (max. 12)

* Datei: `docs/improvement_proposals.md`. Gruppiere nach:
  a) Stabilität/Fehlerpfade/Provider-Fallback
  b) Export/UX/Dateinamensschema
  c) Performance/IO/Cache
  d) Packaging/EXE/Smartscreen
  e) Tests/Coverage
  f) Security/Dependencies
* Für **jeden** Vorschlag angeben:

  * **Kurzbeschreibung**
  * **Nutzen/Impact** (hoch/mittel/niedrig)
  * **Risiko** (gering/mittel/hoch)
  * **Aufwand** (S/M/L)
  * **Akzeptanzkriterien** (prüfbar, messbar)
  * **Betroffene Dateien/Zeilen** (Quellenbezug)
  * **Diff-Entwurf** als **Text** unter `patch_drafts/<slug>.diff` (nur Beispiel-Patch, **nicht** anwenden)

### B2) Roadmap-Entwurf (Papier)

* Ordne die Vorschläge in 2–3 **Hardening-Meilensteine** mit Abhängigkeiten („fertig, wenn …“).
* **Ergebnis:** `docs/hardening_roadmap.md`.

### B3) Management-Kurzbericht

* 1–2 Seiten: **Ist-Stand**, Risiken, **Top-5 Quick Wins** (nur Vorschläge), Aufwandsspannen, **Empfehlung** („Go nach Umsetzung von …“).
* **Ergebnis:** `docs/release_readiness_report.md`.

---

## Beispiel-Befehle (read-only Aktivitäten; Pfade ggf. anpassen)

```powershell
# Hash & Größe der vorhandenen EXE
Get-Item .\LooneyF1Tool.exe | Select-Object Name,Length,LastWriteTime | `
  Out-File .\audit\looney_audit\exe\size_check.txt
Get-FileHash .\LooneyF1Tool.exe -Algorithm SHA256 | `
  Out-File .\audit\looney_audit\exe\hash_old.txt

# Umgebung dokumentieren
python --version | Out-File .\audit\looney_audit\env\env_report.md
pip freeze > .\audit\looney_audit\env\requirements.freeze.txt

# Statische Checks (nur Reports)
ruff check . | Out-File .\audit\looney_audit\static\lint_report.csv
mypy . --install-types --non-interactive > .\audit\looney_audit\static\mypy_report.txt

# Security (nur Reports)
pip-audit -f json -o .\audit\looney_audit\security\pip_audit.json
bandit -r . -q -f txt -o .\audit\looney_audit\security\bandit.txt
```

**Repro-Build (nur, wenn Spec vorhanden; keine Spec-Änderung):**

```powershell
pyinstaller .\LooneyF1Tool.spec --noconfirm --clean `
  | Tee-Object -FilePath .\audit\looney_audit\exe\build_log.txt

Get-FileHash .\dist\LooneyF1Tool\LooneyF1Tool.exe -Algorithm SHA256 `
  | Out-File .\audit\looney_audit\exe\hash_new.txt

fc.exe .\audit\looney_audit\exe\hash_old.txt .\audit\looney_audit\exe\hash_new.txt `
  > .\audit\looney_audit\exe\hash_compare.txt

Get-ChildItem .\dist -Recurse | `
  Out-File .\audit\looney_audit\exe\exe_inventory.md
```

**Smoke-Läufe & Export:**

```powershell
# Hilfe / Start
.\LooneyF1Tool.exe --help 2>&1 | Tee-Object -FilePath .\audit\looney_audit\runtime\smoke_log.txt -Append

# (Beispiel) GUI-Start nachweisbar machen
# → Screenshot manuell als .\audit\looney_audit\screens\gui_start.png speichern

# Export eines bekannten Events
# → erzeugte Datei(en) nach .\audit\looney_audit\samples\ kopieren
# → Dateinamenregelsatz dokumentieren in runtime\filename_checks.md
```

---

## Abgabe (vollständig)

* `docs/inventory.md`, `docs/entrypoints.md`, `docs/claims_traceability.md`
* `env/env_report.md`, `env/requirements.freeze.txt`
* `static/lint_report.csv`, `static/mypy_report.txt`, `static/summary.md`
* `security/pip_audit.json`, `security/bandit.txt`, `security/licenses.csv`, `security/risk_summary.md`
* `exe/size_check.txt`, `exe/hash_old.txt?`, `exe/build_log.txt`, `exe/hash_new.txt?`, `exe/hash_compare.txt?`, `exe/exe_inventory.md`
* `runtime/smoke_log.txt`, `runtime/provider_fallback/*`, `runtime/filename_checks.md`, `samples/*`, `screens/*`
* `docs/export_format_report.md`, `docs/mapping_consistency.md`, `docs/perf_observations.md`, `docs/error_catalog.md`, `docs/release_status_now.md`
* **Vorschläge:** `docs/improvement_proposals.md`, `docs/hardening_roadmap.md`, `patch_drafts/*.diff`
* **Kurzbericht:** `docs/release_readiness_report.md`

**Nochmals: Keine Änderungen am Programmcode oder an Build-Specs. Alle Verbesserungen nur als Vorschläge mit Text-Diffs dokumentieren.**
