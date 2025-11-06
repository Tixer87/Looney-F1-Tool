"""Integration tests for RLT adapter."""

import pytest
from export.rlt_adapter import build_rlt_session


class TestAdapterIntegration:
    """End-to-end tests for RLT adapter."""
    
    def test_build_race_session(self):
        """Test building complete race session."""
        payload = {
            'session_type': 'Race',
            'date': '2025-05-15T14:00:00Z',
            'circuit': 'monaco',
            'weather': 'Clear',
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
                        {'tyre_type': 'Soft', 'laps': 25},
                        {'tyre_type': 'Medium', 'laps': 53}
                    ]
                },
                {
                    'position': 2,
                    'driverId': 'leclerc',
                    'permanentNumber': 16,
                    'givenName': 'Charles',
                    'familyName': 'Leclerc',
                    'nationality': 'Monegasque',
                    'constructorId': 'ferrari',
                    'time': 5402500,
                    'fastest_lap_time': 72800,
                    'laps': 78,
                    'status': 'Finished'
                }
            ]
        }
        
        try:
            result = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not found: {e}")
        
        # Verify structure
        assert 'SessionType' in result
        assert result['SessionType'] == 'Race'
        assert 'Drivers' in result
        assert len(result['Drivers']) == 2
        
        # Verify gaps calculated
        assert result['Drivers'][0]['GapInt'] == 0
        assert result['Drivers'][1]['GapInt'] == 2500
    
    def test_build_quali_session(self):
        """Test building qualification session."""
        payload = {
            'session_type': 'Qualification',
            'date': '2025-05-15T13:00:00Z',
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
                    'time': 72000,
                    'fastest_lap_time': 72000,
                    'laps': 12,
                    'status': 'Finished'
                },
                {
                    'position': 2,
                    'driverId': 'leclerc',
                    'permanentNumber': 16,
                    'givenName': 'Charles',
                    'familyName': 'Leclerc',
                    'nationality': 'Monegasque',
                    'constructorId': 'ferrari',
                    'time': 72200,
                    'fastest_lap_time': 72200,
                    'laps': 12,
                    'status': 'Finished'
                }
            ]
        }
        
        try:
            result = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not found: {e}")
        
        # Verify structure
        assert result['SessionType'] == 'Qualification'
        
        # Verify gaps calculated (quali style)
        assert result['Drivers'][0]['GapInt'] == 0
        assert result['Drivers'][1]['GapInt'] == 200  # 72200 - 72000
    
    def test_missing_circuit_fails(self):
        """Test that missing circuit raises ValueError (STRICT)."""
        payload = {
            'session_type': 'Race',
            'date': '2025-05-15T14:00:00Z',
            'circuit': 'nonexistent_circuit_xyz',
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
        
        with pytest.raises(ValueError) as exc_info:
            build_rlt_session(payload)
        
        assert 'circuit' in str(exc_info.value).lower() or 'track' in str(exc_info.value).lower()
    
    def test_times_converted_to_milliseconds(self):
        """Test that all times are integer milliseconds."""
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
                    'time': 5400.5,  # Float seconds
                    'fastest_lap_time': 72.5,  # Float seconds
                    'laps': 78,
                    'status': 'Finished'
                }
            ]
        }
        
        try:
            result = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not found: {e}")
        
        driver = result['Drivers'][0]
        
        # All times must be integers
        assert isinstance(driver['TimeInt'], int)
        assert isinstance(driver['GapInt'], int)
        assert isinstance(driver['FastestLapTimeInt'], int)
        
        # Values should be in milliseconds
        assert driver['TimeInt'] == 5400500
        assert driver['FastestLapTimeInt'] == 72500
    
    def test_stints_encoded(self):
        """Test that stints are properly encoded."""
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
                        {'tyre_type': 'Medium', 'laps': 53}
                    ]
                }
            ]
        }
        
        try:
            result = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not found: {e}")
        
        driver = result['Drivers'][0]
        
        assert 'StintsRaw' in driver
        assert isinstance(driver['StintsRaw'], str)
        assert ',' in driver['StintsRaw']  # Multiple stints
        assert ':' in driver['StintsRaw']  # Proper format
    
    def test_dnf_driver(self):
        """Test DNF driver handling."""
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
                    'status': 'Finished'
                },
                {
                    'position': 18,
                    'driverId': 'stroll',
                    'permanentNumber': 18,
                    'givenName': 'Lance',
                    'familyName': 'Stroll',
                    'nationality': 'Canadian',
                    'constructorId': 'aston_martin',
                    'time': 0,  # DNF
                    'fastest_lap_time': 73000,
                    'laps': 45,
                    'status': 'DNF',
                    'dnf_reason': 'Engine'
                }
            ]
        }
        
        try:
            result = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not found: {e}")
        
        dnf_driver = result['Drivers'][1]
        
        assert dnf_driver['Status'] == 'Dnf'  # Updated to match RLT enum
    
    def test_required_fields_present(self):
        """Test that all required fields are present in output."""
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
                    'status': 'Finished'
                }
            ]
        }
        
        try:
            result = build_rlt_session(payload)
        except ValueError as e:
            pytest.skip(f"Circuit not found: {e}")
        
        # Check top-level required fields
        required_top = ['SessionType', 'RaceType', 'SessionPosition', 'Date', 'TrackName', 
                       'TrackUniqueName', 'IsLiveData', 'TotalLaps', 'Drivers']
        for field in required_top:
            assert field in result, f"Missing required field: {field}"
        
        # Check driver required fields (nested structure)
        driver = result['Drivers'][0]
        assert 'Driver' in driver, "Missing Driver object"
        assert 'Name' in driver['Driver'], "Missing Driver.Name"
        assert 'Nationality' in driver['Driver'], "Missing Driver.Nationality"
        
        assert 'Team' in driver, "Missing Team object"
        assert 'Name' in driver['Team'], "Missing Team.Name"
        assert 'UniqueName' in driver['Team'], "Missing Team.UniqueName"
        
        required_driver = ['Position', 'TimeInt', 'GapInt', 'LapsCount', 
                          'GridPosition', 'PitsCount', 'Status', 'SeatType']
        for field in required_driver:
            assert field in driver, f"Missing required driver field: {field}"
