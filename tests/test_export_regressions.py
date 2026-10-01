import copy
import pytest
from api import jolpica_api
from api.export_service import run_export,validate_export
from export.rlt_adapter import build_rlt_session
def payload():
    return {"season":2026,"circuit":"Melbourne","session_type":"Race","date":"2026-03-08T15:00:00+11:00","Drivers":[
        {"Driver":{"Name":"Lewis Hamilton"},"RaceNumber":44,"Team":{"Name":"Ferrari"},"Position":1,"Status":"Finished","TimeInt":5000000,"FastestLapTimeInt":80000,"LapsCount":58},
        {"Driver":{"Name":"Max Verstappen"},"RaceNumber":3,"Team":{"Name":"Red Bull Racing"},"Position":2,"Status":"Finished","TimeInt":5001500,"FastestLapTimeInt":80100,"LapsCount":58}
    ]}
def test_preserves_official_results_year_and_source():
    raw=payload()
    original=copy.deepcopy(raw)
    result=build_rlt_session(raw)
    validate_export(result)
    assert raw==original
    assert result["Date"]=="2026-03-08T04:00:00Z"
    assert result["TotalLaps"]==58
    assert result["Drivers"][0]["Team"]["UniqueName"]=="ferrari.2026"
    assert result["Drivers"][1]["RaceNumber"]==3
    assert result["Drivers"][1]["GapInt"]==1500
def test_unknown_race_duration_is_not_a_lap_time():
    raw=payload()
    raw["Drivers"][1]["TimeInt"]=0
    raw["Drivers"][1]["Status"]="Retired"
    result=build_rlt_session(raw)
    assert result["Drivers"][1]["TimeInt"]==0
    assert result["Drivers"][1]["Status"]=="Dnf"
def test_jolpica_never_substitutes_latest_race(monkeypatch):
    def unexpected(*args,**kwargs):
        pytest.fail("unsupported session must not issue a request")
    monkeypatch.setattr(jolpica_api,"_get",unexpected)
    with pytest.raises(ValueError):
        jolpica_api.fetch_results(2024,1,"FP1")
def test_qualifying_reexport_preserves_existing_file(monkeypatch,tmp_path):
    raw=payload()
    for i,row in enumerate(raw["Drivers"]):row.update(Q1=80000+i*100,Q2=79000+i*100,Q3=78000+i*100)
    class Provider:
        name="fastf1"
        def fetch_session_raw(self,*args):
            return copy.deepcopy(raw)
    monkeypatch.setattr("api.export_service.get_provider",lambda **kwargs:Provider())
    run_export(2026,1,"Q",tmp_path)
    first={f.name:f.read_bytes() for f in tmp_path.glob("*.json")}
    run_export(2026,1,"Q",tmp_path)
    assert len(list(tmp_path.glob("*.json")))==6
    assert all((tmp_path/name).read_bytes()==data for name,data in first.items())
def test_live_recording_uses_import_contract():
    from datetime import datetime,timezone
    from live_recorder.state import LiveSessionState,LiveDriverState
    from live_recorder.exporter import LiveToRLTExporter
    state=LiveSessionState(1,"Race","Race","Australian Grand Prix",1,"Melbourne","Australia","AU",2026,datetime(2026,3,8,tzinfo=timezone.utc),"+00:00")
    state.drivers["44"]=LiveDriverState("44","HAM","Lewis Hamilton","L HAMILTON","Lewis","Hamilton","Ferrari","FF0000","GBR",current_position=1,laps_completed=58,best_laptime="1:20.000",finishing_status="Finished")
    data=LiveToRLTExporter(state).export_rlt()
    validate_export(data)
    assert "Meta" not in data
    assert data["session"]["drivers"][0]["fastestLapTimeMs"]==80000
    assert "totalTimeMs" not in data["session"]["drivers"][0]