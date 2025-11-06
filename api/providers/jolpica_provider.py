# api/providers/jolpica_provider.py
from __future__ import annotations
from . import jolpica_api as api

class JolpicaProvider:
    name = "jolpica"

    @staticmethod
    def is_available() -> bool:
        return api.healthcheck()

    def schedule(self, year: int) -> list[dict]:
        raw = api.fetch_schedule(year)
        races = raw.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        out = []
        for r in races:
            out.append({
                "year": year,
                "round": int(r.get("round", 0)),
                "raceName": r.get("raceName", ""),
                "circuitFullName": r.get("Circuit", {}).get("circuitName", ""),
                "date": r.get("date", ""),
                "time": r.get("time", ""),
            })
        return out

    def fetch_session_raw(self, year: int, round_no: int, session_type: str) -> dict:
        """
        Liefert normalisiertes Payload mit Drivers-Array für export_service.
        """
        results = api.fetch_results(year, round_no, session_type)
        
        # Extract Drivers from Ergast response
        races = results.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        
        # Ergast uses different keys for Race vs Qualifying
        if races:
            race = races[0]
            # Check for QualifyingResults (Quali) or Results (Race)
            drivers_raw = race.get("QualifyingResults", race.get("Results", []))
        else:
            drivers_raw = []
        
        # Normalize to expected format
        drivers = []
        leader_time_str = None  # Will be set from P1
        
        for d in drivers_raw:
            driver_info = d.get("Driver", {})
            constructor_info = d.get("Constructor", {})
            position = d.get("position", "")
            
            # Extract time string
            time_str = d.get("Time", {}).get("time", "") if d.get("Time") else ""
            
            # For P1, this is the total time (e.g., "1:31:44.742")
            # For P2+, this is the gap (e.g., "+22.457")
            if position == "1":
                leader_time_str = time_str
            
            drivers.append({
                "DriverNumber": driver_info.get("permanentNumber") or driver_info.get("code", "99"),
                "Abbreviation": driver_info.get("code", ""),
                "FirstName": driver_info.get("givenName", ""),
                "LastName": driver_info.get("familyName", ""),
                "nationality": driver_info.get("nationality", ""),  # ✅ NEW: Nationality for rlt_adapter
                "Team": constructor_info.get("name", ""),
                "TeamColor": constructor_info.get("constructorId", ""),
                "Constructor": constructor_info,  # ✅ Pass full constructor for rlt_adapter
                "Position": position,
                "GridPosition": d.get("grid", ""),
                "Status": d.get("status", ""),
                "Time": time_str,  # For P1: total time, For P2+: gap string (e.g., "+22.457")
                "LeaderTime": leader_time_str if position != "1" else "",  # ✅ NEW: Leader time for gap calculation
                "Points": d.get("points", "0"),
                "FastestLapTime": d.get("FastestLap", {}).get("Time", {}).get("time", "") if d.get("FastestLap") else "",
                "FastestLapNumber": d.get("FastestLap", {}).get("lap", "0") if d.get("FastestLap") else "0",
                "Laps": d.get("laps", "0"),  # ✅ NEW: Laps completed
            })
        
        return {
            "provider": self.name,
            "year": year,
            "round": round_no,
            "sessionType": session_type,
            "Drivers": drivers,  # ✅ Normalized drivers array
            "ergast": results,  # Keep raw data for debugging
        }