"""Provider locations must map to the actual venue, including relocated races."""
import json
from pathlib import Path

import pytest

from mapping.circuit_aliases import get_circuit


def test_2026_calendar_locations():
    rows = json.loads((Path(__file__).parent / 'fixtures/calendar_2026_locations.json').read_text())
    assert len(rows) == 23
    for row in rows:
        assert get_circuit(row['location'])[1] == row['track']


@pytest.mark.parametrize('name,expected', [
    ('Monte Carlo', 'monaco.2015'),
    ('Miami Gardens', 'miami.2022'),
    ('Madrid', 'madrid.2026'),
    ('Kuala Lumpur', 'sepang.1999'),
    ('Sepang International Circuit', 'sepang.1999'),
    ('Madring Street Circuit', 'madrid.2026'),
])
def test_provider_venue_aliases(name, expected):
    assert get_circuit(name)[1] == expected
    assert get_circuit({'circuitName': name})[1] == expected


def test_unknown_location_is_not_guessed():
    with pytest.raises(ValueError):
        get_circuit('Monte Carlo Unknown Layout')
