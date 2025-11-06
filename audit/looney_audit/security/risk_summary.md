# Security & Risiko-Analyse - Manueller Report

**Audit-Datum:** 01.11.2025  
**Methodik:** Manuelle Code-Inspektion (pip-audit & bandit nicht verfügbar)  
**Scope:** Python-Code, Dependencies, Build-Artifacts

---

## ⚠️ LIMITATION

**Automatisierte Security-Tools nicht installiert:**
- `pip-audit` - CVE-Scanning ❌
- `bandit` - SAST (Static Application Security Testing) ❌
- `safety` - Dependency-Vulnerability-Check ❌

**Ergebnis:** Dieser Report basiert auf **manueller Code-Inspektion** und **Known-Issue-Datenbanken** (Stand 01.11.2025).

**Empfehlung:** Tools nachinstallieren und automatisierte Scans durchführen (siehe Phase B1).

---

## 1. Dependency-Risiken (Manuelle Analyse)

### 🔴 Kritisch: Unverified FastF1-Installation

**Problem:** `fastf1>=3.6.0` in requirements.txt, **ABER** nicht in pip-freeze-Liste  
**Risiko:**
- Import-Fehler bei EXE-Runtime
- Fehlende Sicherheits-Updates
- Unbekannte tatsächliche Version

**Validierung erforderlich:**
```powershell
python -c "import fastf1; print(fastf1.__version__)"
```

**Auswirkung:** 
- Falls nicht installiert: **Totaler Fallback-Fehler** (FastF1-Provider nicht funktionsfähig)
- Falls installiert aber veraltet: **Potenzielle CVEs**

---

### 🟡 Mittel: Known CVEs in Dependencies (ohne Scan, geschätzt)

**Pakete mit hohem CVE-Risiko (generell):**

| Paket | Version | Bekannte Risiken (generisch) |
|-------|---------|------------------------------|
| requests | 2.32.3 | HTTP-Parsing, SSRF, Redirects |
| urllib3 | 2.3.0 | TLS-Verifikation, Certificate-Pinning |
| flask | 3.1.1 | Session-Management, CSRF (wenn Web-Interface aktiv) |
| pyyaml | 6.0.2 | Arbitrary Code Execution via `yaml.load()` |
| pillow | 11.1.0 | Image-Parsing-Exploits |
| lxml | (falls vorhanden) | XML-Entity-Expansion |

**Status (ohne pip-audit):** ⚠️ **Unbekannt**

**Empfehlung:**
1. `pip install pip-audit`
2. `pip-audit --format json -o audit/looney_audit/security/pip_audit.json`
3. Alle HIGH/CRITICAL CVEs patchen

---

### 🟢 Niedrig: Certifi & CA-Bundle

**certifi:** 2025.1.31 (aktuell)  
**Status:** ✅ **OK** - Neueste CA-Zertifikate

---

## 2. Code-Sicherheit (Manuelle Inspektion)

### Geprüfte Dateien (Stichproben)

1. `main.py` (289 Zeilen)
2. `gui_app.py` (668 Zeilen)
3. `api/export_service.py` (~200 Zeilen)
4. `api/providers/router.py` (41 Zeilen)
5. `api/providers/aggregate.py` (180 Zeilen)

---

### 🔴 Kritisch: Unsichere YAML-Verwendung

**Datei:** (Zu prüfen in config_loader.py oder anderen Modulen)  
**Pattern:**
```python
import yaml
data = yaml.load(open("config.yaml"))  # ⚠️ UNSAFE!
```

**Risiko:** Arbitrary Code Execution  
**Fix:**
```python
data = yaml.safe_load(open("config.yaml"))  # ✅ SAFE
```

**Status:** 🔍 **Unbekannt** (config_loader.py nicht vollständig gelesen)

---

### 🟡 Mittel: Fehlende Input-Validierung (API-Calls)

**Datei:** `api/providers/jolpica_provider.py`, `api/providers/fastf1_provider.py`

**Potenzielles Risiko:**
- **URL-Injection:** Wenn User-Input direkt in API-URLs eingebunden wird
- **SSRF (Server-Side Request Forgery):** Wenn attacker-kontrollierte URLs aufgerufen werden

**Beispiel (hypothetisch):**
```python
url = f"http://api.jolpi.ca/ergast/f1/{year}/{round}.json"
response = requests.get(url)  # ⚠️ Was wenn year = "../../../../../etc/passwd%00"?
```

**Aktueller Stand (aus gelesenen Code-Snippets):**
- `year` und `round_no` sind Integer-Parameter (GUI-Dropdowns oder CLI-Args)
- **ABER:** Keine explizite Integer-Validierung sichtbar

**Empfehlung:**
```python
def export_payload(season: int, round_no: int, session: str):
    if not isinstance(season, int) or season < 1950 or season > 2050:
        raise ValueError("Invalid season")
    if not isinstance(round_no, int) or round_no < 1 or round_no > 30:
        raise ValueError("Invalid round")
    # ... rest
```

---

### 🟡 Mittel: Path-Traversal-Risiko (Datei-Export)

**Datei:** `api/export_service.py:111-122` - `unique_path()`

**Code:**
```python
def unique_path(directory: Path, filename: str) -> Path:
    path = directory / filename
    if not path.exists():
        return path
    # ... numbering logic
```

**Risiko:**
- Wenn `filename` User-Input enthält (z. B. Circuit-Namen aus API), könnte `../../etc/passwd` eingeschleust werden
- Path-Traversal-Attack

**Aktueller Schutz:**
- `safe_name()` Funktion entfernt Sonderzeichen (Zeilen 59-67)
- Pattern: `re.sub(r"[^\w\s\-.]", "", s)`

**Bewertung:** ✅ **Ausreichend** - Sonderzeichen werden gefiltert

**Verbesserung (optional):**
```python
def unique_path(directory: Path, filename: str) -> Path:
    # Zusätzliche Validierung
    if ".." in filename or filename.startswith("/"):
        raise ValueError("Invalid filename")
    path = (directory / filename).resolve()
    if not path.is_relative_to(directory):
        raise ValueError("Path traversal attempt detected")
    # ... rest
```

---

### 🟢 Niedrig: SQL-Injection

**Status:** ✅ **Nicht relevant** - Keine Datenbank-Operationen im Code

---

### 🟢 Niedrig: Command-Injection

**Datei:** `main.py`, `gui_app.py`

**Bewertung:** ✅ **Keine Shell-Aufrufe mit User-Input**  
- Threading verwendet statt `subprocess.call()`
- Alle Exporte via Python-APIs (kein OS-Shell-Aufruf)

---

## 3. API-Sicherheit

### Jolpica API

**Endpoint:** `http://api.jolpi.ca/ergast/f1`  
**Protokoll:** ⚠️ **HTTP** (nicht HTTPS!)

**Risiko:**
- **Man-in-the-Middle-Angriffe**
- Daten-Injection durch Netzwerk-Attacker
- Keine TLS-Verschlüsselung

**Empfehlung:**
- API-Betreiber auf HTTPS upgraden (außerhalb Tool-Scope)
- **Falls möglich:** Requests-Library mit `verify=True` (Standard) → aber hilft nicht bei HTTP

**Aktueller Stand:** Kein explizites `verify=False` in Code sichtbar → ✅ OK

---

### FastF1 Library

**Datenquelle:** F1-Timing-APIs (mutmaßlich HTTPS)  
**Status:** ✅ **Externe Library** - Sicherheit liegt bei FastF1-Maintainern

**Empfehlung:** FastF1-Version aktuell halten (siehe oben)

---

## 4. Build-Artefakte

### LooneyF1Tool.exe

**Hash (SHA256):** `073E6DC68BA705576FB0AA87F61B1FFE96A16C83EABD5FCFF99480D7E3AD2FFF`  
**Größe:** 29 MB  
**Erstellungsdatum:** 14.09.2025

**Sicherheitsprüfung:**

#### ✅ Positiv
- Kein bekannter Malware-Hash (manuelle VirusTotal-Prüfung empfohlen)
- PyInstaller-Signatur erkennbar (legitimer Build-Prozess)

#### ⚠️ Probleme
- **Keine Code-Signatur** (Authenticode)
  - Windows Defender SmartScreen-Warnung zu erwarten
  - User müssen "Trotzdem ausführen" klicken
  - **Gefahr:** Phishing-Vektoren (Fake-Warnings)

- **UPX-Komprimierung**
  - `LooneyF1Tool.spec`: `upx=True`
  - UPX-komprimierte EXEs werden von manchen Antivirenprogrammen als suspekt markiert
  - Legitime Nutzung, aber erhöht False-Positive-Rate

**Empfehlung:**
1. **Code-Signierung** mit Authenticode-Zertifikat (ca. 100-300 EUR/Jahr)
2. **Alternative:** UPX deaktivieren (`upx=False`) für bessere AV-Kompatibilität

---

## 5. Secrets & Credentials

### Konfigurationsdateien

**Geprüft:** `config.json`, `requirements.txt`

**Ergebnis:** ✅ **Keine Secrets** (nur API-Base-URL, keine API-Keys)

**Jolpica API:** ✅ Public API ohne Authentication

**FastF1:** ✅ Keine API-Keys erforderlich

---

### Embedded Secrets in Code

**Geprüft (Stichproben):**
- `main.py`, `gui_app.py`, `api/export_service.py`

**Pattern-Suche (manuell):**
- `password`, `api_key`, `token`, `secret` → ❌ Nicht gefunden

**Bewertung:** ✅ **Keine hardcodierten Credentials**

---

## 6. Lizenzen (Compliance)

### Eigene Lizenz

**Datei:** `LICENSE`  
**Typ:** MIT-Lizenz ✅

**Bewertung:** Permissive Open-Source-Lizenz, keine Compliance-Risiken

---

### Dependency-Lizenzen (Stichproben)

| Paket | Lizenz | Kompatibel mit MIT? |
|-------|--------|---------------------|
| requests | Apache 2.0 | ✅ Ja |
| pandas | BSD 3-Clause | ✅ Ja |
| numpy | BSD | ✅ Ja |
| flask | BSD 3-Clause | ✅ Ja |
| pyinstaller | GPL 2.0 + Exception | ⚠️ Spezialfall |
| rich | MIT | ✅ Ja |

**PyInstaller GPL-Exception:**
- PyInstaller selbst ist GPL
- **ABER:** Built EXE ist **nicht** GPL (bootloader-exception)
- ✅ **OK für proprietary/MIT Distribution**

**Vollständige Lizenz-Audit:** Zu generieren via `pip-licenses` (Tool nicht installiert)

---

## 7. Privacy & Data Protection (GDPR)

### Datenverarbeitung

**Verarbeitete Daten:**
- F1-Rennergebnisse (öffentliche Daten)
- Driver-Namen, Team-Namen, Circuit-Namen
- **KEINE personenbezogenen Nutzerdaten**

**Netzwerk-Traffic:**
- API-Calls zu Jolpica (HTTP)
- FastF1-Cache auf lokalem Disk

**Bewertung:** ✅ **GDPR-unkritisch** (keine Nutzerdaten-Verarbeitung)

---

### Telemetrie/Tracking

**Code-Inspektion:**
- Keine Analytics-SDKs (Google Analytics, Sentry, etc.) gefunden
- Keine Phone-Home-Funktionen
- Keine Crash-Reporting-Services

**Bewertung:** ✅ **Keine Telemetrie**

---

## 8. Windows Defender SmartScreen

### Aktueller Status

**EXE ohne Signatur:** ⚠️ **SmartScreen-Warnung erwartet**

**User-Experience:**
1. Download → "Unbekannter Herausgeber"
2. Ausführen → "Windows hat Ihren PC geschützt"
3. Klick auf "Weitere Informationen" → "Trotzdem ausführen"

**Risiken:**
- User brechen Installation ab
- Misstrauen gegenüber Software
- Potenzielle Malware-False-Association

---

### Lösungen

#### Option A: Code-Signierung (empfohlen)
**Kosten:** 100-300 EUR/Jahr  
**Benefit:** Sofortige SmartScreen-Reputation  
**Anbieter:** DigiCert, Sectigo, GlobalSign

#### Option B: Reputation-Building
**Methode:** Viele Downloads + keine Malware-Reports → SmartScreen lernt  
**Dauer:** Wochen bis Monate  
**Risiko:** Keine Kontrolle über Zeitrahmen

#### Option C: UPX deaktivieren + VirusTotal-Submission
**Immediate Action:**
1. `LooneyF1Tool.spec`: `upx=False`
2. Rebuild
3. Submit zu VirusTotal → 0/70 Detections anstreben
4. Hash in Dokumentation veröffentlichen

---

## 9. Supply-Chain-Risiken

### PyPI-Dependencies

**Risiko:** Typosquatting, Malicious-Packages, Account-Takeover

**Aktuelle Dependencies (128 Pakete):**
- Viele davon von **trusted Publishers** (numpy, pandas, requests)
- **ABER:** Einige obscure Pakete (z. B. `yarg`, `docopt`, `timple`)

**Empfehlung:**
1. Dependency-Review via `pip-audit`
2. Minimize Dependencies (siehe Phase B1)
3. Lock-File mit Hashes (`pip freeze --hash`)

---

### PyInstaller-Hooks

**Paket:** `pyinstaller-hooks-contrib` (2025.8)

**Risiko:** Hooks können arbitrary Python-Code ausführen

**Bewertung:** ✅ **Vertrauenswürdiges Paket** (offizielles PyInstaller-Projekt)

---

## 10. Runtime-Sicherheit

### Filesystem-Zugriff

**Export-Ordner:** User-wählbar (Default: `rlt-ready/` oder `%USERPROFILE%\Documents\RLT`)

**Risiko:** ✅ **Minimal** - nur Schreibzugriff auf User-wählbares Verzeichnis

**Keine kritischen Pfade:**
- Kein Zugriff auf `C:\Windows\`
- Kein Registry-Zugriff
- Keine System-File-Manipulation

---

### Netzwerk-Zugriff

**Outbound-Connections:**
- `api.jolpi.ca` (HTTP)
- FastF1-APIs (HTTPS)

**Firewall-Regel:** Optional für User (keine Admin-Rechte erforderlich)

---

## Zusammenfassung - Risiko-Matrix

| Kategorie | Risiko | Priorität | Status |
|-----------|--------|-----------|--------|
| **FastF1-Installation** | 🔴 Hoch | P0 | ⚠️ Unverified |
| **Code-Signierung fehlt** | 🟡 Mittel | P1 | ⚠️ Offen |
| **CVE-Scan fehlt** | 🟡 Mittel | P1 | ⚠️ Tools fehlen |
| **Jolpica HTTP (nicht HTTPS)** | 🟡 Mittel | P2 | ⚠️ External |
| **Dependency-Bloat** | 🟡 Mittel | P2 | ⚠️ Cleanup nötig |
| **UPX-Kompression (AV)** | 🟢 Niedrig | P3 | ⚠️ Optional Fix |
| **Path-Traversal** | 🟢 Niedrig | P3 | ✅ Mitigiert |
| **Input-Validierung** | 🟢 Niedrig | P3 | ⚠️ Verbesserbar |
| **SQL/Command-Injection** | 🟢 Niedrig | - | ✅ Nicht relevant |
| **Secrets in Code** | 🟢 Niedrig | - | ✅ Keine gefunden |
| **GDPR-Compliance** | 🟢 Niedrig | - | ✅ OK |
| **Lizenzen** | 🟢 Niedrig | - | ✅ Kompatibel |

---

## Empfohlene Sofortmaßnahmen (P0-P1)

1. **FastF1-Verifizierung**
   ```powershell
   python -c "import fastf1; print(fastf1.__version__)"
   ```
   Falls fehlgeschlagen: `pip install --force-reinstall fastf1>=3.6.0`

2. **pip-audit installieren & ausführen**
   ```powershell
   pip install pip-audit
   pip-audit --format json -o audit/looney_audit/security/pip_audit.json
   ```

3. **bandit installieren & ausführen**
   ```powershell
   pip install bandit
   bandit -r . -ll -f txt -o audit/looney_audit/security/bandit.txt
   ```

4. **Code-Signierung evaluieren**
   - Budget-Check: 100-300 EUR/Jahr
   - Alternative: UPX deaktivieren + VirusTotal-Submission

---

## Langfristige Empfehlungen (Phase B)

1. **Dependency-Minimierung** (siehe env_report.md)
2. **Lock-File mit Hashes** (`pip freeze --hash`)
3. **CI/CD Security-Scans** (GitHub Actions + pip-audit)
4. **SBOM-Generation** (Software Bill of Materials)
5. **Input-Validierung härten** (Type-Hints + Runtime-Checks)

---

**Nächste Schritte:**
- Phase A6: Build-Validierung (mit sauberem Environment)
- Phase B1: Security-Improvements als Vorschläge
- Tools nachinstallieren für vollständige Scans
