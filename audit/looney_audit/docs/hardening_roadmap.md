# Hardening-Roadmap: Looney F1 Tool v1.6

**Erstellt:** 01.11.2025  
**Zweck:** Priorisierte Roadmap für Release-Readiness

---

## Meilenstein 1: **Minimum Viable Release** (1-2 Tage)

**Ziel:** Kritische Blocker beheben → Salonfähig mit Einschränkungen (60/100)  
**Zielgruppe:** Early Adopters, Technical Users

### Tasks

| ID | Task | Aufwand | Abhängigkeiten | Akzeptanzkriterium |
|----|------|---------|----------------|---------------------|
| A1 | FastF1-Installation verifizieren | 1h | - | Import erfolgreich, in pip-freeze |
| A2 | Provider-Fallback-Tests | 3h | A1 | 3 Test-Cases dokumentiert |
| D1 | UPX deaktivieren | 15min | - | Rebuild erfolgreich |
| D2 | Dependency-Cleanup | 4-6h | - | EXE < 20 MB |

**Gesamt:** 8-11 Stunden

**Deliverables:**
1. FastF1 funktionsfähig
2. Provider-Tests dokumentiert (`audit/runtime/smoke_log.txt`)
3. EXE ohne UPX, < 20 MB
4. Clean requirements-prod.txt

**Fertig, wenn:**
- Alle 4 Tasks abgeschlossen
- Smoke-Tests erfolgreich (GUI + CLI)
- EXE startet ohne Fehler

---

## Meilenstein 2: **Security & Stability Hardening** (1-2 Tage)

**Ziel:** Security-Baseline + Code-Qualität → Production-Ready (85/100)  
**Zielgruppe:** Allgemeine User, Non-Technical

### Tasks

| ID | Task | Aufwand | Abhängigkeiten | Akzeptanzkriterium |
|----|------|---------|----------------|---------------------|
| F1 | pip-audit & bandit | 1-2h | - | Keine HIGH/CRITICAL CVEs |
| A3 | Exception-Spezifität | 2-3h | - | Logging statt `pass` |
| A4 | Export-Loop-Error-Handling | 1h | - | Bulk-Export robust |
| B1 | Timestamp-Filename (optional) | 1h | - | Optional implementiert |

**Gesamt:** 5-7 Stunden

**Deliverables:**
1. Security-Reports (`audit/security/pip_audit.json`, `bandit.txt`)
2. Improved Exception-Handling
3. Robust Bulk-Export
4. Optional: Timestamp-Feature

**Fertig, wenn:**
- Keine kritischen Security-Befunde
- Exception-Handling spezifisch
- "All Sessions" Export überlebt Teilfehler

---

## Meilenstein 3: **Professional Polish** (2-3 Tage, optional)

**Ziel:** Enterprise-Grade (95/100)  
**Zielgruppe:** Professionelle User, Langzeit-Wartbarkeit

### Tasks

| ID | Task | Aufwand | Abhängigkeiten | Akzeptanzkriterium |
|----|------|---------|----------------|---------------------|
| D3 | Code-Signierung | 4h Setup | Budget-Freigabe | EXE signiert, kein SmartScreen |
| F3 | Logging-Framework | 3-4h | - | logging statt print |
| E1 | Test-Coverage erhöhen | 6-8h | - | > 60% Coverage |
| B2 | Progress-Indikator | 2-3h | - | GUI zeigt Progress |

**Gesamt:** 15-19 Stunden

**Deliverables:**
1. Signierte EXE (SmartScreen-frei)
2. Einheitliches Logging-System
3. Test-Coverage > 60%
4. GUI-Verbesserungen

**Fertig, wenn:**
- EXE ohne SmartScreen-Warnung
- Alle Module nutzen `logging`
- pytest-cov > 60%
- Progress-Bar funktioniert

---

## Dependency-Graph

```
Meilenstein 1 (Blocker-Fixes)
├─ A1: FastF1-Verify
│  └─ A2: Provider-Tests (benötigt A1)
├─ D1: UPX off
└─ D2: Dependency-Cleanup

Meilenstein 2 (Security/Stability)
├─ F1: Security-Audit (parallel)
├─ A3: Exception-Handling (parallel)
├─ A4: Export-Loop (parallel)
└─ B1: Timestamp (optional, parallel)

Meilenstein 3 (Polish)
├─ D3: Code-Signing (Budget-abhängig)
├─ F3: Logging (benötigt A3 teilweise)
├─ E1: Tests (parallel)
└─ B2: Progress (parallel)
```

---

## Zeitplan (Beispiel)

### Woche 1: Minimum Viable Release

**Tag 1-2:**
- Morning: A1 (1h)
- Afternoon: A2 (3h)
- Evening: D1 (15min)

**Tag 2-3:**
- Full Day: D2 (4-6h)
- Testing: Smoke-Tests

**Delivery:** Minimum-Release (60/100)

---

### Woche 2: Hardening

**Tag 3-4:**
- Morning: F1 (2h)
- Afternoon: A3 (3h)
- Evening: A4 (1h)

**Tag 4-5:**
- Morning: B1 (1h, optional)
- Testing: Regression-Tests

**Delivery:** Production-Ready (85/100)

---

### Woche 3-4: Polish (optional)

**Tag 5-6:**
- D3: Code-Signing-Setup (4h)

**Tag 7-8:**
- F3: Logging-Framework (3-4h)

**Tag 9-10:**
- E1: Test-Coverage (6-8h)

**Tag 11:**
- B2: Progress-Indikator (2-3h)

**Delivery:** Enterprise-Grade (95/100)

---

## Resource-Planung

### Minimum-Release (Meilenstein 1)
**Developer:** 1 Person  
**Zeit:** 1-2 Tage  
**Budget:** ~400-480 EUR (@ 40 EUR/h)

### Production-Ready (Meilenstein 1+2)
**Developer:** 1 Person  
**Zeit:** 3-4 Tage  
**Budget:** ~880-1.120 EUR

### Enterprise-Grade (Meilenstein 1+2+3)
**Developer:** 1 Person  
**Zeit:** 6-8 Tage  
**Budget:** ~1.880-2.720 EUR

---

## Release-Kriterien pro Meilenstein

### Meilenstein 1: ✅ Go-Kriterien
- [ ] FastF1 installiert & getestet
- [ ] 3 Provider-Test-Cases dokumentiert
- [ ] EXE ohne UPX, Größe < 20 MB
- [ ] Dependency-Cleanup abgeschlossen
- [ ] Smoke-Tests erfolgreich (GUI + CLI)

### Meilenstein 2: ✅ Go-Kriterien
- [ ] pip-audit: Keine HIGH/CRITICAL CVEs
- [ ] bandit: Keine kritischen Befunde
- [ ] Exception-Handling spezifisch
- [ ] "All Sessions" Export robust
- [ ] Regression-Tests erfolgreich

### Meilenstein 3: ✅ Go-Kriterien
- [ ] EXE signiert (SmartScreen-frei)
- [ ] Logging-Framework vollständig
- [ ] Test-Coverage > 60%
- [ ] Progress-Indikator funktioniert
- [ ] Performance-Baseline erfüllt

---

## Risiken & Mitigation

### Risiko 1: FastF1 nicht installierbar
**Wahrscheinlichkeit:** Niedrig  
**Impact:** Hoch (Blocker)  
**Mitigation:** Falls Problem: Fallback nur auf Jolpica dokumentieren, FastF1 als "Zukunfts-Feature"

### Risiko 2: Dependency-Cleanup bricht Build
**Wahrscheinlichkeit:** Mittel  
**Impact:** Mittel  
**Mitigation:** Inkrementelles Vorgehen, nach jedem entfernten Paket testen

### Risiko 3: Code-Signing-Budget nicht verfügbar
**Wahrscheinlichkeit:** Hoch  
**Impact:** Niedrig (Workaround vorhanden)  
**Mitigation:** SmartScreen-Anleitung in README (bereits in D1/D2 enthalten)

---

## Empfohlener Pfad

**Für schnellen Community-Release:** Meilenstein 1 + 2 (3-4 Tage)  
**Für professionellen Launch:** Meilenstein 1 + 2 + 3 (6-8 Tage)

**Management-Entscheidung erforderlich für:** Meilenstein 3 (Budget für Code-Signierung)

---

**Status:** Roadmap-Entwurf (nicht umgesetzt, Read-Only Audit)
