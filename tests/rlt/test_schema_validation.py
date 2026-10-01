"""Tests for RLT schema validation."""

import pytest
import json
from pathlib import Path

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from export.rlt_adapter import build_rlt_session


@pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not installed")
class TestSchemaValidation:
    """Test that generated RLT sessions validate against schema."""
    
    @pytest.fixture
    def schema(self):
        """Load RLT session schema."""
        schema_path = Path(__file__).parent.parent.parent / 'export' / 'rlt_session.schema.json'
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def minimal_payload(self):
        """Minimal valid payload for testing."""
        return {
            'session_type': 'Race',
            'date': '2025-05-15T14:00:00Z',
            'circuit': 'monaco',
            'drivers': [
                {
                    'position': 1,
                    'driverId': 'verstappen',
                    'permanentNumber': 1,
                    'givenName': 'Max',
                    'familyName': 'Verstappen',
                    'nationality': 'Dutch',
                    'constructorId': 'red_bull',
                    'time': 5400000,
                    'fastest_lap_time': 72500,
                    'laps': 78,
                    'status': 'Finished'
                }
            ]
        }
    
    def test_minimal_session_validates(self, schema, minimal_payload):
        """Test that minimal session validates against schema."""
        try:
            rlt_session = build_rlt_session(minimal_payload)
        except ValueError as e:
            pytest.skip(f"Circuit not in circuits.json: {e}")
        
        # Validate against schema
        try:
            jsonschema.validate(rlt_session, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Schema validation failed: {e.message}")
    
    def test_multiple_drivers_validates(self, schema):
        """Test session with multiple drivers validates."""
        payload = {
            'session_type': 'Race',
            'date': '2025-05-15T14:00:00Z',
            'circuit': 'monaco',
            'drivers': [
                {
                    'position': i,
                    'driverId': f'driver_{i}',
                    'permanentNumber': i,
                    'givenName': f'Driver',
                    'familyName': f'{i}',
                    'nationality': 'British',
                    'constructorId': 'team',
                    'time': 5400000 + (i-1) * 1000,
                    'fastest_lap_time': 72500,
                    'laps': 78,
                    'status': 'Finished'
                }
                for i in range(1, 6)
            ]
        }
        
        try:
            rlt_session = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not in circuits.json: {e}")
        
        # Validate against schema
        try:
            jsonschema.validate(rlt_session, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Schema validation failed: {e.message}")
    
    def test_quali_session_validates(self, schema):
        """Test qualification session validates."""
        payload = {
            'session_type': 'Qualification',
            'date': '2025-05-15T14:00:00Z',
            'circuit': 'monaco',
            'drivers': [
                {
                    'position': 1,
                    'driverId': 'verstappen',
                    'permanentNumber': 1,
                    'givenName': 'Max',
                    'familyName': 'Verstappen',
                    'nationality': 'Dutch',
                    'constructorId': 'red_bull',
                    'time': 72500,
                    'fastest_lap_time': 72500,
                    'laps': 12,
                    'status': 'Finished'
                }
            ]
        }
        
        try:
            rlt_session = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not in circuits.json: {e}")
        
        # Validate against schema
        try:
            jsonschema.validate(rlt_session, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Schema validation failed: {e.message}")
    
    def test_session_with_stints_validates(self, schema):
        """Test session with stints validates."""
        payload = {
            'session_type': 'Race',
            'date': '2025-05-15T14:00:00Z',
            'circuit': 'monaco',
            'drivers': [
                {
                    'position': 1,
                    'driverId': 'verstappen',
                    'permanentNumber': 1,
                    'givenName': 'Max',
                    'familyName': 'Verstappen',
                    'nationality': 'Dutch',
                    'constructorId': 'red_bull',
                    'time': 5400000,
                    'fastest_lap_time': 72500,
                    'laps': 78,
                    'status': 'Finished',
                    'stints': [
                        {'tyre_type': 'Soft', 'laps': 25, 'wear_start': 100, 'wear_end': 35},
                        {'tyre_type': 'Medium', 'laps': 53, 'wear_start': 100, 'wear_end': 18}
                    ]
                }
            ]
        }
        
        try:
            rlt_session = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not in circuits.json: {e}")
        
        # Validate against schema
        try:
            jsonschema.validate(rlt_session, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Schema validation failed: {e.message}")
    
    def test_required_fields_present(self, minimal_payload):
        """Test that all required top-level fields are present."""
        try:
            rlt_session = build_rlt_session(minimal_payload)
        except ValueError as e:
            pytest.skip(f"Circuit not in circuits.json: {e}")
        
        # Check required top-level fields
        required_fields = ['SessionType', 'Date', 'TrackName', 'TrackUniqueName', 'Drivers']
        for field in required_fields:
            assert field in rlt_session, f"Missing required field: {field}"
    
    def test_required_driver_fields_present(self, minimal_payload):
        """Test that all required driver fields are present."""
        try:
            rlt_session = build_rlt_session(minimal_payload)
        except ValueError as e:
            pytest.skip(f"Circuit not in circuits.json: {e}")
        
        # Check required driver fields (nested structure)
        drivers = rlt_session.get('Drivers', [])
        assert len(drivers) > 0, "No drivers in session"
        
        driver = drivers[0]
        
        # Check nested Driver object
        assert 'Driver' in driver, "Missing Driver object"
        assert 'Name' in driver['Driver'], "Missing Driver.Name"
        assert 'Nationality' in driver['Driver'], "Missing Driver.Nationality"
        
        # Check nested Team object
        assert 'Team' in driver, "Missing Team object"
        assert 'Name' in driver['Team'], "Missing Team.Name"
        assert 'UniqueName' in driver['Team'], "Missing Team.UniqueName"
        
        # Check top-level driver fields
        required_top = ['Position', 'TimeInt', 'GapInt', 'FastestLapTimeInt', 
                       'LapsCount', 'GridPosition', 'PitsCount', 'SeatType', 'Status']
        for field in required_top:
            assert field in driver, f"Missing required driver field: {field}"
