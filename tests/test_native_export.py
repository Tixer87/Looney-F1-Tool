import copy
from uuid import UUID
from export.native_rlt import build_native_session
from api.export_service import validate_export
from tests.test_export_regressions import payload


def sample():
    p = payload()
    p.update(round=1, has_sprint=False)
    p['Drivers'][0].update(GridPosition=3, Points='25')
    p['Drivers'][1].update(GridPosition=6, Points='18')
    return p


def test_native_race_structure_and_real_points():
    p=sample(); original=copy.deepcopy(p)
    result=build_native_session(p); validate_export(result)
    assert p == original
    assert set(result)=={'metadata','season','event','session'}
    info=result['session']['sessionInfo']
    UUID(info['sessionId'])
    assert info['raceType']=='Main' and info['completedStatus']=='Completed'
    a,b=result['session']['drivers']
    assert a['driverPoints']=='25' and a['gap']=='0' and a['gapMs']==0
    assert b['gap']=='+1.500' and b['intervalMs']==1500
    assert b['positionChange']==4 and b['classificationPosition']==2
    assert b['driverInfo']['raceNumber']=='3'
    assert a['totalTimeMs']==5000000 and a['totalTime']=='83:20.000'
    assert a['team']['uniqueId']=='ferrari.2026'
    assert 'weatherType' not in info
    assert 'laps' not in a and 'stints' not in a


def test_dnf_and_lapped_are_distinct():
    for status,expected,classification in [('Collision','DNF',-1),('+2 Laps','Finished',2),('Did not start','DNS',-1),('Disqualified','DSQ',-1)]:
        p=sample();p['Drivers'][1].update(Status=status,LapsCount=56,TimeInt=0,Points='0')
        result=build_native_session(p);validate_export(result)
        row=result['session']['drivers'][1]
        assert row['status']==expected and row['classificationPosition']==classification
        assert row['position']==2 and row['gapMs']==2000000000 and row['gap']=='+2 Laps'
        assert 'totalTime' not in row and 'totalTimeMs' not in row


def test_practice_and_qualifying_use_same_envelope():
    for kind,phase in [('Practice',None),('Qualification','Q2')]:
        p=sample();p['session_type']=kind
        if phase:
            p['_current_q_session']=phase
            p['qual_type']=phase
            for i,row in enumerate(p['Drivers']):row.update(Q1=81000+i*200,Q2=80000+i*200)
        result=build_native_session(p);validate_export(result)
        assert result['session']['sessionInfo']['sessionType']==kind
        assert 'raceDetails' not in result['session']
        assert len(result['session']['drivers'])==2
        if phase: assert result['session']['sessionInfo']['sessionPosition']==1


def test_unknown_points_are_not_invented():
    result=build_native_session(payload())
    assert 'driverPoints' not in result['session']['drivers'][0]
