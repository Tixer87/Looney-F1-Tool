import pytest
import requests
from api.providers import fallback
from api.providers.openf1_provider import OpenF1Provider


class Primary:
    name = 'fastf1'
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error
    def fetch_session_raw(self, *args):
        if self.error:
            raise self.error
        return self.result


@pytest.mark.parametrize('result', [{'Drivers': [{'Position': 1}]}, {'Drivers': []}])
def test_reachable_primary_never_uses_openf1(monkeypatch, result):
    monkeypatch.setattr(OpenF1Provider, 'fetch_session_raw', lambda *a: pytest.fail('OpenF1 called'))
    monkeypatch.setattr(fallback.JolpicaProvider, 'fetch_session_raw', lambda *a: {'Drivers': []})
    fallback.fetch_with_fallback(Primary(result), 2026, 6, 'R')


def test_both_existing_sources_must_be_down(monkeypatch):
    calls = []
    def outage(*a):
        raise requests.Timeout('test outage')
    monkeypatch.setattr(fallback.JolpicaProvider, 'fetch_session_raw', outage)
    monkeypatch.setattr(OpenF1Provider, 'fetch_session_raw', lambda *a: calls.append(a) or {'Drivers': [1]})
    assert fallback.fetch_with_fallback(Primary(error=requests.ConnectionError()), 2026, 6, 'R')['Drivers']
    assert len(calls) == 1


def test_empty_secondary_blocks_openf1(monkeypatch):
    monkeypatch.setattr(fallback.JolpicaProvider, 'fetch_session_raw', lambda *a: {'Drivers': []})
    monkeypatch.setattr(OpenF1Provider, 'fetch_session_raw', lambda *a: pytest.fail('OpenF1 called'))
    assert fallback.fetch_with_fallback(Primary(error=requests.Timeout()), 2026, 6, 'R') is None


def test_data_errors_do_not_trigger_openf1(monkeypatch):
    monkeypatch.setattr(OpenF1Provider, 'fetch_session_raw', lambda *a: pytest.fail('OpenF1 called'))
    with pytest.raises(ValueError):
        fallback.fetch_with_fallback(Primary(error=ValueError('bad data')), 2026, 6, 'R')


def test_practice_outage_can_fall_back_without_unsupported_jolpica(monkeypatch):
    monkeypatch.setattr(fallback.JolpicaProvider, 'fetch_session_raw', lambda *a: pytest.fail('unsupported Jolpica'))
    monkeypatch.setattr(OpenF1Provider, 'fetch_session_raw', lambda *a: {'Drivers': [1]})
    assert fallback.fetch_with_fallback(Primary(error=requests.Timeout()), 2026, 6, 'FP1')['Drivers']


def test_openf1_unclassified_driver_and_seconds_conversion(monkeypatch):
    from api.providers import openf1_provider as op
    def get(endpoint, **kwargs):
        return {
            'sessions': [{'date_start': '2026-06-07T13:00:00+00:00', 'session_key': 1, 'circuit_short_name': 'Monte Carlo'}],
            'session_result': [
                {'driver_number': 44, 'position': 1, 'duration': 5000.123, 'number_of_laps': 78},
                {'driver_number': 16, 'position': None, 'duration': None, 'number_of_laps': 50, 'dnf': True}],
            'drivers': [{'driver_number': n, 'first_name': f, 'last_name': l, 'team_name': 'Ferrari'} for n,f,l in [(44,'Lewis','Hamilton'),(16,'Charles','Leclerc')]],
            'starting_grid': [],
        }[endpoint]
    monkeypatch.setattr(op, '_get', get)
    rows = OpenF1Provider().fetch_session_raw(2026, 6, 'R')['Drivers']
    assert rows[0]['TimeInt'] == 5000123
    assert rows[0]['GridPosition'] == 0
    assert rows[1]['Position'] == 2
    assert rows[1]['Status'] == 'Retired'
    assert rows[1]['TimeInt'] == 0
