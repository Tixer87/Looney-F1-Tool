# f1-dash Integration Analysis
**Projekt:** Looney F1 Tool - Live Recording Feature  
**Fork:** https://github.com/Tixer87/f1-dash  
**Datum:** 21. November 2025  
**Status:** Schritt 1 - Bestandsaufnahme abgeschlossen

---

## 1. f1-dash Architektur Überblick

f1-dash ist ein Rust-basiertes Live-Telemetrie-System für F1, bestehend aus mehreren Services:

### Services
- **`live`** (Port 4000): SSE-Server für Live-Streaming von F1-Daten
- **`api`** (Port 4001): REST API für Schedule/Health
- **`analytics`** (Port 4002): TimescaleDB für historische Laptime/Gap-Analysen
- **`importer`**: Speichert Live-Daten in TimescaleDB
- **`dash`**: Next.js Frontend (React/TypeScript)

### Crates
- **`client`**: F1 SignalR Client (verbindet zu `livetiming.formula1.com`)
- **`timescale`**: PostgreSQL/TimescaleDB Datenbankschicht
- **`data`**: JSON Merge-Logik für State-Updates

---

## 2. Relevante Endpoints für Live Recording

### 2.1 Live Service (`localhost:4000`)

#### **GET `/api/sse`**
**Format:** Server-Sent Events (SSE)  
**Events:**
- `initial`: Kompletter initialer State beim Verbindungsaufbau
- `update`: Inkrementelle Updates während der Session

**Initial Event Payload:**
```json
{
  "sessionInfo": {
    "meeting": { "key": 1234, "name": "São Paulo Grand Prix", ... },
    "type": "Race",              // "Race", "Qualifying", "Sprint", "Practice"
    "name": "Race",
    "startDate": "2025-11-03T17:00:00Z",
    "gmtOffset": "03:00:00",
    "key": 9999
  },
  "sessionStatus": { "status": "Started" },  // "Finished", "Finalised"
  "trackStatus": { "status": "1", "message": "AllClear" },
  "driverList": {
    "1": {
      "racingNumber": "1",
      "tla": "VER",
      "fullName": "Max Verstappen",
      "teamName": "Red Bull Racing",
      "teamColour": "3671C6",
      "countryCode": "NED"
    }
  },
  "lapCount": { "currentLap": 1, "totalLaps": 71 },
  "timingData": {
    "sessionPart": 1,            // Qualifying: 1=Q1, 2=Q2, 3=Q3
    "lines": {
      "1": {
        "racingNumber": "1",
        "position": "1",
        "gapToLeader": "0.0",
        "intervalToPositionAhead": { "value": "0.273", "catching": false },
        "lastLapTime": { "value": "1:21.306", "status": 2048 },
        "bestLapTime": { "value": "1:20.123", "status": 2048 },
        "sectors": [
          { "value": "26.259", "status": 2048, "personalFastest": true, "overallFastest": false },
          ...
        ],
        "inPit": false,
        "pitOut": false,
        "retired": false,
        "stopped": false,
        "numberOfLaps": 10
      }
    }
  },
  "timingAppData": {
    "lines": {
      "1": {
        "racingNumber": "1",
        "gridPos": "1",
        "stints": [
          { "compound": "SOFT", "totalLaps": 10, "new": "TRUE" },
          { "compound": "MEDIUM", "totalLaps": 5, "new": "FALSE" }
        ]
      }
    }
  },
  "raceControlMessages": {
    "messages": [
      {
        "utc": "2025-11-03T17:05:23Z",
        "lap": 3,
        "category": "SafetyCar",
        "message": "SAFETY CAR DEPLOYED",
        "flag": "YELLOW",
        "scope": "Track"
      }
    ]
  },
  "weatherData": {
    "airTemp": "28.5",
    "trackTemp": "42.3",
    "humidity": "65",
    "rainfall": "0",
    "windSpeed": "12",
    "windDirection": "180"
  }
}
```

**Update Event Payload (Partial):**
```json
{
  "lapCount": { "currentLap": 2 },
  "timingData": {
    "lines": {
      "1": {
        "lastLapTime": { "value": "1:20.456" }
      }
    }
  }
}
```

#### **GET `/api/drivers`**
Liefert `driverList` als Array (ohne SSE).

#### **GET `/api/health`**
Health Check: `{"success": true}`

### 2.2 API Service (`localhost:4001`)

#### **GET `/api/schedule`**
Liefert kompletten F1-Kalender des aktuellen Jahres.

#### **GET `/api/schedule/next`**
Liefert nächstes Event.

**Response:**
```json
{
  "name": "São Paulo Grand Prix",
  "countryName": "Brazil",
  "start": "2025-11-01T10:00:00Z",
  "end": "2025-11-03T20:00:00Z",
  "sessions": [
    { "kind": "Practice 1", "start": "...", "end": "..." },
    { "kind": "Sprint Qualifying", "start": "...", "end": "..." },
    { "kind": "Sprint", "start": "...", "end": "..." },
    { "kind": "Qualifying", "start": "...", "end": "..." },
    { "kind": "Race", "start": "...", "end": "..." }
  ],
  "over": false
}
```

### 2.3 Analytics Service (`localhost:4002`)

#### **GET `/api/laptime/{driver_nr}`**
Historische Laptimes pro Runde (aus TimescaleDB).

#### **GET `/api/gap/{driver_nr}`**
Gap-Historie pro Fahrer.

---

## 3. Datenstrukturen (TypeScript/Rust Models)

### 3.1 Session Info
```typescript
type SessionInfo = {
  meeting: {
    key: number;
    name: string;              // "São Paulo Grand Prix"
    location: string;
    circuit: { key: number; shortName: string };
    country: { code: string; name: string };
  };
  type: string;                // "Race", "Qualifying", "Sprint"
  name: string;
  startDate: string;
  endDate: string;
  gmtOffset: string;
  key: number;
};
```

### 3.2 Driver (Live State)
```typescript
type Driver = {
  racingNumber: string;        // "1"
  tla: string;                 // "VER"
  fullName: string;
  broadcastName: string;
  teamName: string;
  teamColour: string;          // Hex ohne #
  firstName: string;
  lastName: string;
  countryCode: string;         // "NED"
};
```

### 3.3 Timing Data (Pro Fahrer)
```typescript
type TimingDataDriver = {
  racingNumber: string;
  position: string;            // "1", "2", ...
  gapToLeader: string;         // "0.0", "+5.432"
  intervalToPositionAhead?: { value: string; catching: boolean };
  lastLapTime: { value: string; status: number };  // "1:21.306"
  bestLapTime: { value: string; status: number };
  sectors: Sector[];           // 3 Sektoren
  numberOfLaps: number;
  inPit: boolean;
  pitOut: boolean;
  retired: boolean;
  stopped: boolean;
  knockedOut?: boolean;        // Qualifying
};

type Sector = {
  value: string;               // "26.259"
  status: number;              // 2048 = valid
  personalFastest: boolean;
  overallFastest: boolean;
  segments: { status: number }[];  // Mini-Sectors
};
```

### 3.4 Stints (Reifen & Boxenstopps)
```typescript
type TimingAppDataDriver = {
  racingNumber: string;
  gridPos: string;             // Startposition
  stints: Stint[];
};

type Stint = {
  totalLaps?: number;          // Runden auf diesem Reifensatz
  compound?: "SOFT" | "MEDIUM" | "HARD" | "INTERMEDIATE" | "WET";
  new?: "TRUE" | "FALSE";      // Neu oder gebraucht
};
```

**Pitstop-Logik:**
- Anzahl Stints = Anzahl Pitstops + 1
- `gridPos` = Startposition
- Letzter Stint in Array = aktueller Reifen

### 3.5 Race Control Messages
```typescript
type Message = {
  utc: string;
  lap: number;
  message: string;             // "SAFETY CAR DEPLOYED"
  category: "SafetyCar" | "Flag" | "Drs" | "Other";
  flag?: "YELLOW" | "RED" | "GREEN" | "CHEQUERED";
  scope?: "Track" | "Driver" | "Sector";
};
```

**Wichtige Kategorien:**
- `SafetyCar`: VSC / SC Events
- `Flag`: Red Flag, Green Flag
- `Other`: Track Limits, Penalties

### 3.6 Lap Count
```typescript
type LapCount = {
  currentLap: number;
  totalLaps: number;
};
```

### 3.7 Track/Session Status
```typescript
type TrackStatus = {
  status: string;              // "1" = AllClear, "4" = Yellow, "6" = VSC, "7" = SC
  message: string;
};

type SessionStatus = {
  status: "Started" | "Finished" | "Finalised" | "Ends";
};
```

### 3.8 Weather
```typescript
type WeatherData = {
  airTemp: string;             // Celsius
  trackTemp: string;
  humidity: string;            // Prozent
  rainfall: string;            // "0" oder "1"
  windSpeed: string;           // km/h
  windDirection: string;       // Grad
};
```

---

## 4. Event-Flow für Live Recording

### 4.1 Verbindungsaufbau
1. **EventSource** öffnen zu `http://localhost:4000/api/sse`
2. **`initial`-Event** empfangen → Kompletter State
3. **`update`-Events** empfangen → Inkrementelle Änderungen

### 4.2 State Management
- **Initial:** Baseline State speichern
- **Updates:** Per JSON Pointer Merge (z.B. `/timingData/lines/1/lastLapTime/value`)
- **Reconnect:** Bei Verbindungsabbruch automatisch reconnecten

### 4.3 Datenextraktion während Session

**Pro Update:**
```
IF lapCount.currentLap changed:
  → Neue Runde begonnen
  → Für alle Fahrer: Laptimes/Sectors extrahieren

IF timingAppData.lines[nr].stints.length increased:
  → Pitstop erkannt
  → Stint-Wechsel: compound, totalLaps speichern

IF raceControlMessages new entry:
  → Safety Car / VSC / Red Flag / Penalty
  → Event-Log ergänzen

IF timingData.lines[nr].retired = true:
  → DNF erkannt
  → Finishing Status setzen
```

### 4.4 Session Ende
```
WHEN sessionStatus.status = "Finished":
  → Finalen State freezen
  → Für alle Fahrer:
    - Endposition aus timingData.lines[nr].position
    - Gesamt-Runden = lapCount.currentLap
    - Pitstops = stints.length - 1
  → RLT JSON Export generieren
```

---

## 5. Mapping zu RLT JSON

### 5.1 Meta Block
```json
{
  "Event": sessionInfo.meeting.name,          // "São Paulo Grand Prix"
  "Track": sessionInfo.meeting.circuit.shortName,
  "Year": parse(sessionInfo.startDate).year,
  "Session": sessionInfo.type,                // "Race", "Qualifying"
  "Date": sessionInfo.startDate,
  "Weather": {
    "AirTemp": weatherData.airTemp,
    "TrackTemp": weatherData.trackTemp,
    "Rainfall": weatherData.rainfall == "1"
  },
  "RaceControl": {
    "SafetyCarCount": count(raceControlMessages where category="SafetyCar" and message contains "SAFETY CAR"),
    "VirtualSafetyCarCount": count(... "VIRTUAL SAFETY CAR"),
    "RedFlagCount": count(raceControlMessages where flag="RED")
  }
}
```

### 5.2 Driver Block (Pro Fahrer)
```json
{
  "Name": driverList[nr].fullName,
  "Number": driverList[nr].racingNumber,
  "Team": map via teams_aliases(driverList[nr].teamName),
  "Nation": map via drivers_nations(driverList[nr].countryCode),
  "StartPosition": timingAppData.lines[nr].gridPos,
  "EndPosition": timingData.lines[nr].position,
  "Laps": lapCount.currentLap,
  "Status": retired ? "DNF" : "Finished",
  "Pitstops": [
    {
      "Lap": calculate from stint transitions,
      "Compound": stint.compound,
      "StopCount": index + 1
    }
  ]
}
```

### 5.3 Bestehende Looney F1 Mappings nutzen

**Driver Mapping:**
- `drivers_aliases.py` → Name/TLA → RLT ID
- `drivers_nations.py` → Country Code → Nation

**Team Mapping:**
- `teams_aliases.py` → Team Name → RLT Team ID
- `teams.f1.json` → Team Metadata

**Circuit Mapping:**
- `circuit_aliases.py` → Meeting Name → Circuit Name
- `circuits.json` → Circuit Metadata

---

## 6. Technische Anforderungen für Looney F1 Tool

### 6.1 Dependencies
```txt
# Python SSE Client
sseclient-py==1.8.0  # oder httpx für AsyncIO
requests>=2.31.0
```

### 6.2 Neue Module

```
looney_f1_tool/
├── api/
│   └── f1dash_client.py         # SSE Client für /api/sse
├── live_recorder/
│   ├── __init__.py
│   ├── session_state.py         # Session State Klasse
│   ├── event_processor.py       # Event -> State Update
│   ├── pitstop_detector.py      # Stint-Change Detection
│   ├── race_control_parser.py   # SC/VSC/Red Flag
│   └── exporter.py              # Live State -> RLT JSON
└── backends/
    └── f1dash_live.py           # Backend Profile
```

### 6.3 CLI Command
```bash
python main.py \
  --backend f1dash_live \
  --mode record \
  --f1dash-url http://localhost:4000 \
  --output-dir ./output/live
```

### 6.4 Session State Klasse (Entwurf)
```python
@dataclass
class LiveSessionState:
    # Meta
    session_info: dict
    weather: dict
    
    # Drivers
    drivers: Dict[str, LiveDriverState]
    
    # Race Control
    safety_car_count: int = 0
    vsc_count: int = 0
    red_flag_count: int = 0
    
    # Timing
    current_lap: int = 0
    total_laps: int = 0
    session_status: str = "Started"

@dataclass
class LiveDriverState:
    number: str
    tla: str
    full_name: str
    team_name: str
    country_code: str
    
    start_position: int
    current_position: int
    
    laps_completed: int
    best_laptime: Optional[str]
    last_laptime: Optional[str]
    
    stints: List[StintData]
    pitstops: List[PitstopData]
    
    in_pit: bool = False
    retired: bool = False
    dnf: bool = False
```

---

## 7. Nicht verfügbare Daten & Workarounds

### Nicht direkt aus f1-dash:
- **Penalties:** Nur via RaceControlMessages Text-Parsing
- **DRS Zones:** Nicht verfügbar (nur ob Fahrer DRS hat)
- **Stint Start Lap:** Muss aus Stint-Transitions berechnet werden
- **Exact Pitstop Duration:** Nicht direkt, nur via Laptime-Differenz schätzbar

### Mögliche Ergänzungen:
- **Jolpica Fallback:** Nach Session-Ende Jolpica abfragen für missing data
- **FastF1 Merge:** Qualifying Grid Positions / Race Stint Details

---

## 8. Nächste Schritte

**✅ Schritt 1 abgeschlossen:** Bestandsaufnahme f1-dash

**→ Schritt 2:** Konzept für Live Recorder Modul
- Session State Klassen definieren
- Event Processing Pipeline skizzieren
- Mapping zu RLT JSON Schema

**→ Schritt 3:** Backend-Profil `f1dash_live` implementieren
- SSE Client
- State Management
- Logging

**→ Schritt 4:** Event-Verarbeitung
- Lap Detection
- Pitstop Detection
- Race Control Parsing

**→ Schritt 5:** Export-Pfad
- Live State → RLT JSON Adapter
- Bestehende Mappings integrieren

**→ Schritt 6:** Tests
- Mock f1-dash Responses
- 5-Runden-Simulation
- Export Validation

---

## 9. Offene Fragen

1. **Docker vs. Local f1-dash?**
   - Soll f1-dash automatisch gestartet werden oder manuell?
   - Docker-Compose Integration?

2. **Reconnect-Strategie?**
   - Wie lange retry bei Verbindungsabbruch?
   - State Recovery nach Reconnect?

3. **Partial Sessions?**
   - Recording mittendrin starten?
   - Oder nur von Session-Start an?

4. **Output Format?**
   - Nur finaler JSON am Ende?
   - Oder auch Zwischenstände?

---

**Ende Schritt 1 Bestandsaufnahme**
