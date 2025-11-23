# F1 DASH - FORK
**Titel:** Looney F1 – Live Recorder über f1 dash Fork (RLT Export nach Live Session)

Du arbeitest als KI in VSCode in meinem lokalen Setup.
Deine Aufgabe: Für das **Looney F1 Tool** eine **Live-Aufzeichnung über f1 dash** integrieren, die am Ende einen **sauberen, fertigen JSON-Export für das Racing League Tools (RLT)** erzeugt.

---

## 1. Kontext & Repos

**Meine Projekte:**

* Looney F1 Tool (Python):
  – Exportiert aktuell F1-Daten (Jolpica / FastF1) in ein **RLT-kompatibles JSON**
  – Es gibt saubere Mappings für Fahrer, Teams, Nationen und Strecken in separaten Python-Modulen, z. B.:

  * `drivers_aliases.py`
  * `drivers_nations.py`
  * `teams_aliases.py` / `teams.f1.json`
  * `circuit_aliases.py` / `circuits.json`
  * `lineups.f1.json`
    – Diese Mapping-Layer sind die „Single Source of Truth“ für das RLT-Schema

* Datenquellen bisher:

  * **Jolpica F1 API** → Hauptquelle für Sessions, Laps, Stints etc.
  * **FastF1** → Zusatz / Fallback für bestimmte Daten
  * Ziel: Offline / On-Demand Export eines fertigen RLT-JSONs

**Neues Repo für Live:**

* Ich habe **f1 dash geforkt**:
  `https://github.com/Tixer87/f1-dash`
* Das ist ein Rust-Backend mit Telemetrie für F1 (offizieller Stream), plus Frontend
* Wichtig: Du arbeitest ab jetzt primär mit **meinem Fork** (`Tixer87/f1-dash`), nicht mit dem Original

---

## 2. Ziel des neuen Features

Ich möchte im Looney F1 Tool ein neues Feature:

> **Live Aufzeichnung über f1 dash, die am Ende einen fertigen RLT-Export produziert.**

Konkret:

* Während einer laufenden F1 Session (Race, Quali etc.) soll **f1 dash** die Telemetrie liefern
* Looney F1 soll:

  * sich an f1 dash „andröpseln“
  * die Session **live mitschneiden**
  * intern einen Session-State aufbauen (Driver, Stints, Boxenstopps, SC/VSC, Red Flags usw.)
  * bei „Recording Stopp“ einen **RLT-kompatiblen JSON-Export** erzeugen

Wichtig:
Ich will **keine Live-Auswertung für Zuschauer**, sondern am Ende einen **sauberen finalen Export**, plus ein paar sinnvolle Logs während des Mitschnitts.

---

## 3. Anforderungen an die Live-Integration

### 3.1 Rolle von f1 dash

* f1 dash soll als **externer Backend-Service** laufen (Docker oder lokal)
* Lizenzthema: f1 dash (AGPL) bleibt ein **eigenes Projekt**. Looney F1 konsumiert nur die **öffentliche API** meines Forks
* Keine direkte Copy-Paste-Übernahme von Kernlogik aus f1 dash in Looney F1

**Deine Aufgabe hier:**

* Analysiere meinen Fork `Tixer87/f1-dash`
* Finde heraus:

  * Welche Endpoints / Streams eignen sich für:

    * Session Info (Track, Year, Session Type)
    * Drivers / Constructors
    * Lap Data (LapTimes, Sectors)
    * Tyres / Compounds
    * Flags (VSC, SC, Red Flag)
    * Pits / Pitstop Events
  * In welchem Format die Daten zurückkommen (JSON, SSE, Websocket etc.)
* Dokumentiere intern (als Kommentar oder Markdown im Projekt), welche Endpoints du verwenden willst

### 3.2 Neues Backend-Profil im Looney F1 Tool

In Looney F1 sollst du ein **neues Backend-Profil** einführen, z. B.:

* `backend = "f1dash_live"` oder ähnlich

Dieses Profil:

* Nutzt **nicht** Jolpica / FastF1, sondern **nur f1 dash** als Datenquelle
* Verwendet aber das **bestehende Mapping / Export-System**:

  * Driver werden über `drivers_aliases` / `drivers.json` gemappt
  * Teams über `teams.f1.json` / `teams_aliases`
  * Strecken über `circuits.json` / `circuit_aliases`
* Ziel bleibt ein **RLT-kompatibles JSON** mit meinem bisherigen Meta + Driver Blocks

### 3.3 Live Recorder Flow

Baue bitte einen klaren, robusten Flow (vorerst CLI-basiert, keine fancy GUI nötig):

1. **Start Live Recording**

   * Befehl im Looney F1 Tool, z. B.:

     * `python main.py --backend f1dash_live --mode record --session <SESSION_ID|AUTO>`
   * Das Tool:

     * Verbindet sich mit f1 dash
     * Ermittelt Session Metadaten:

       * Jahr
       * Strecke
       * Session-Typ (Race / Quali / Sprint etc.)
       * Event-Name
     * Initialisiert einen internen Session State (Python Klassen / Data Classes)

2. **Während der Session**

   * Looney F1:

     * Abonniert den Live-Stream / Events von f1 dash (je nach Implementierung: Polling, SSE, Websocket)
     * Aktualisiert bei jedem Event den Session State:

       * Fahrerstatus (DRS, On-Track, Pit, DNF, DNS etc. – soweit verfügbar)
       * Rundenzeiten, Sektoren
       * Boxenstopps (Lap, Tyre In/Out, Stop-Dauer)
       * SC / VSC / Red Flag Events (Anzahl, Phasen)
       * Stints (Tyre Stint Blöcke pro Fahrer)
     * Schreibt einfache Logs:

       * Minimal: Konsole
       * Optional: Logdatei (z. B. `logs/live_record_<session>.log`)
   * Wichtig:

     * Robust gegen Verbindungsabbrüche
     * Falls f1 dash kurz nicht antwortet, soll der Recorder versuchen zu reconnecten, ohne das ganze Programm abzuschiessen

3. **Stop Recording & Export**

   * Am Ende der Session (oder wenn ich abbreche):

     * „Freeze“ den letzten konsistenten Session State
     * Erzeuge daraus:

       * Meta Block (Event, Strecke, Datum, Session Type, Wetter falls verfügbar)
       * Driver Blocks gemäß RLT-Schema:

         * Name, Nummer, Team, Nation (über bestehende Mapping-Getter)
         * Startposition, Endposition
         * Rundenanzahl
         * Pitstops (inkl. Runde, Compound, Stopcount)
         * Info zur Race Control (z. B. SC/VSC/Red Flag Counts auf Session-Level)
     * Exportiere ein **RLT-kompatibles JSON** in den üblichen Output-Ordner des Looney F1 Tools

---

## 4. Daten, die für RLT besonders wichtig sind

Beim Live Mitschnitt sollen vor allem die Infos sauber eingefangen werden, die für RLT-Overlays / Randbilder relevant sind:

* **Pitstops pro Fahrer**

  * Runde des Stops
  * Anzahl Stops
  * Tyre Wechsel (Compound, ggf. In/Out)
* **Race Control Events**

  * Anzahl Virtual Safety Car Phasen
  * Anzahl Safety Car Phasen
  * Anzahl Red Flags
* **Finishing Status**

  * DNF / DSQ / DNS (so gut wie f1 dash das hergibt)
* **Basis Timing**

  * Startposition
  * Endposition
  * Gesamt Rundenanzahl (für das Resultat)

Wenn f1 dash bestimmte Details nicht liefert, baue bitte eine klare Stelle im Code ein, wo später zusätzliche Quellen (z. B. Jolpica/Ergebnis als Fallback) „drüber gemerged“ werden könnten. Vorläufig reicht: So viel wie möglich aus f1 dash konsistent mitschneiden.

---

## 5. Nicht-Ziele und Grenzen

* **Jolpica / FastF1 Workflows nicht anfassen**

  * Bestehender Offline Export über Jolpica / FastF1 muss funktionieren wie vorher
  * Kein Refactoring quer durchs Projekt, nur dort wo es für die Live-Integration nötig ist
* **Keine neue Monster-Architektur**

  * Saubere Modulstruktur ja, aber bitte pragmatisch
* **Kein Zuschauer-Live-Dashboard bauen**

  * Fokus liegt auf dem **Recording** und dem finalen **Export**
* **Keine Lizenz-Falle**

  * f1 dash bleibt ein externer Service (mein Fork)
  * Looney F1 konsumiert nur die API, der Projektcode bleibt sauber getrennt

---

## 6. Arbeitsstil und Vorgehen

Bitte arbeite in **klaren, nummerierten Schritten** mit Zustandsprüfung, damit wir keine Loops und keine doppelten Implementierungen produzieren.

Konkrete Bitte:

1. **Bestandsaufnahme f1 dash**

   * Analysiere meinen Fork
   * Dokumentiere kurz:

     * Relevante Endpoints / Streams
     * Datenstrukturen (z. B. JSON Felder für Laps, Pits, Flags)
   * Prüfe, ob und wie Session IDs / Events identifiziert werden

2. **Konzept für Live Recorder Modul**

   * Skizziere ein neues Modul / Package im Looney F1 Tool, z. B. `live_recorder/` oder ähnliches
   * Definiere:

     * zentrale Klassen / Strukturen für Session State
     * Schnittstelle zur f1 dash API
     * Schnittstelle zum bestehenden Export (Mapping + RLT JSON Builder)
   * Erst wenn diese Skizze steht, dann implementieren

3. **Implementierung Backend-Profil f1dash_live**

   * Neues Backend Profil integrieren
   * Live Recorder Command implementieren (CLI-Eintrag)
   * Verbindung zu f1 dash herstellen, Session State aufbauen

4. **Event-Verarbeitung & State-Update**

   * Event-Loop / Streaming implementieren
   * Mapping von f1 dash Daten → interner State
   * Logs implementieren

5. **Export Pfad**

   * Existing RLT-Exportlogik nutzen
   * Falls nötig: Adapter bauen, der den Live-Session-State in die schon existierenden Exportfunktionen einspeist

6. **Tests**

   * Unit-Tests für:

     * Mapping f1 dash → interner State
     * Export aus Live-State → RLT JSON
   * Wenn möglich: Simulierter Input (Mock f1 dash Responses) für einen kurzen Testlauf (z. B. 5 Runden, 1 Pit, 1 VSC)

Wichtig:
Bitte keine „optional“, „vielleicht“, „könnten wir noch“ Vorschläge. Ich will konkrete, klar definierte Schritte, die du direkt im Code umsetzt: inklusive Einbindung in die Engine, Fehlerbehandlung, Logging und Tests.

---

Das ist der komplette Rahmen. Nutze meinen Fork `Tixer87/f1-dash` als Telemetrie-Quelle, integriere einen robusten Live Recorder im Looney F1 Tool und sorge dafür, dass am Ende ein sauberer, RLT-kompatibler JSON-Export aus dieser Live-Aufzeichnung entsteht.