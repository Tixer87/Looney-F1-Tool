from api import jolpica_api as api
class JolpicaProvider:
    name="jolpica"
    @staticmethod
    def is_available()->bool:
        return api.healthcheck()
    def schedule(self,year:int)->list[dict]:
        races=api.fetch_schedule(year).get("MRData",{}).get("RaceTable",{}).get("Races",[])
        return [{"year":year,"round":int(r.get("round",0)),"raceName":r.get("raceName",""),"circuitFullName":r.get("Circuit",{}).get("circuitName",""),"date":r.get("date",""),"time":r.get("time","")} for r in races]
    def fetch_session_raw(self,year:int,round_no:int,session_type:str)->dict:
        from export.rlt_adapter import _to_milliseconds
        code="Q" if session_type in ("Q1","Q2","Q3") else session_type
        if code not in ("R","Q","S"):return {"Drivers":[]}
        races=api.fetch_results(year,round_no,code).get("MRData",{}).get("RaceTable",{}).get("Races",[])
        if not races:return {"Drivers":[]}
        race=races[0]
        rows=race.get({"R":"Results","Q":"QualifyingResults","S":"SprintResults"}[code],[])
        drivers=[]
        for row in rows:
            person=row["Driver"]
            fastest=row.get("FastestLap",{})
            entry={
                "Driver":{"Name":person["givenName"]+" "+person["familyName"],"_nationality_raw":person.get("nationality","")},
                "RaceNumber":str(row.get("number") or person.get("permanentNumber","")),
                "Team":{"Name":row["Constructor"]["name"],"_constructorId":row["Constructor"]["constructorId"]},
                "Position":int(row["position"]),
                "GridPosition":int(row.get("grid",0)),
                "Status":row.get("status","Ok"),
                "TimeInt":int(row.get("Time",{}).get("millis",0)),
                "FastestLapTimeInt":_to_milliseconds(fastest.get("Time",{}).get("time","")),
                "FastestLapNumLap":int(fastest.get("lap",0)),
                "LapsCount":int(row.get("laps",0)),
                "PitsCount":0
            }
            if code=="Q":
                for q in ("Q1","Q2","Q3"):entry[q]=row.get(q,"")
            if row.get("points") is not None:entry["Points"]=str(row["points"])
            drivers.append(entry)
        return {"provider":self.name,"season":year,"round":round_no,"circuit":race["Circuit"]["circuitName"],"date":race["date"]+"T"+race.get("time","00:00:00Z"),"Drivers":drivers}