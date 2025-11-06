"""Tests for gap calculation logic (Race vs Quali)."""

import pytest
from export.rlt_adapter import _calculate_gaps_race, _calculate_gaps_quali


class TestGapsLogic:
    """Test gap calculation for Race and Qualification sessions."""
    
    def test_race_gaps_leader_zero(self):
        """Test that race leader has GapInt=0."""
        drivers = [
            {'Position': 1, 'Name': 'Leader', 'TimeInt': 90000, 'Laps': 50, 'FastestLapTimeInt': 1800}
        ]
        
        result = _calculate_gaps_race(drivers)
        assert result[0]['GapInt'] == 0
    
    def test_race_gaps_calculated_correctly(self):
        """Test that race gaps are time behind leader."""
        drivers = [
            {'Position': 1, 'Name': 'P1', 'TimeInt': 90000, 'Laps': 50, 'FastestLapTimeInt': 1800},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 91000, 'Laps': 50, 'FastestLapTimeInt': 1810},
            {'Position': 3, 'Name': 'P3', 'TimeInt': 91500, 'Laps': 50, 'FastestLapTimeInt': 1820}
        ]
        
        result = _calculate_gaps_race(drivers)
        
        assert result[0]['GapInt'] == 0
        assert result[1]['GapInt'] == 1000  # 91000 - 90000
        assert result[2]['GapInt'] == 1500  # 91500 - 90000
    
    def test_race_gaps_lapped_drivers(self):
        """Test that lapped drivers have GapInt=0."""
        drivers = [
            {'Position': 1, 'Name': 'P1', 'TimeInt': 90000, 'Laps': 50, 'FastestLapTimeInt': 1800},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 90500, 'Laps': 49, 'FastestLapTimeInt': 1810}  # Lapped
        ]
        
        result = _calculate_gaps_race(drivers)
        
        assert result[0]['GapInt'] == 0
        assert result[1]['GapInt'] == 0  # Lapped, so gap is 0
    
    def test_race_gaps_never_negative(self):
        """Test that gaps are never negative."""
        drivers = [
            {'Position': 1, 'Name': 'P1', 'TimeInt': 90000, 'Laps': 50, 'FastestLapTimeInt': 1800},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 89000, 'Laps': 50, 'FastestLapTimeInt': 1810}  # Invalid data
        ]
        
        result = _calculate_gaps_race(drivers)
        
        # Gap should be clamped to 0, not negative
        assert result[1]['GapInt'] >= 0
    
    def test_race_gaps_not_equal_to_laptime(self):
        """Test critical validation: GapInt must NOT equal FastestLapTimeInt."""
        drivers = [
            {'Position': 1, 'Name': 'P1', 'TimeInt': 90000, 'Laps': 50, 'FastestLapTimeInt': 1800},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 91000, 'Laps': 50, 'FastestLapTimeInt': 1000}  # Gap would be 1000
        ]
        
        # This should raise AssertionError because GapInt (1000) == FastestLapTimeInt (1000)
        with pytest.raises(AssertionError) as exc_info:
            _calculate_gaps_race(drivers)
        
        assert 'GapInt' in str(exc_info.value) and 'FastestLapTimeInt' in str(exc_info.value)
    
    def test_quali_gaps_pole_zero(self):
        """Test that pole position has GapInt=0."""
        drivers = [
            {'Position': 1, 'Name': 'Pole', 'TimeInt': 72000, 'FastestLapTimeInt': 72000}
        ]
        
        result = _calculate_gaps_quali(drivers)
        assert result[0]['GapInt'] == 0
    
    def test_quali_gaps_calculated_correctly(self):
        """Test that quali gaps are time behind pole."""
        drivers = [
            {'Position': 1, 'Name': 'P1', 'TimeInt': 72000, 'FastestLapTimeInt': 72000},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 72200, 'FastestLapTimeInt': 72200},
            {'Position': 3, 'Name': 'P3', 'TimeInt': 72500, 'FastestLapTimeInt': 72500}
        ]
        
        result = _calculate_gaps_quali(drivers)
        
        assert result[0]['GapInt'] == 0
        assert result[1]['GapInt'] == 200   # 72200 - 72000
        assert result[2]['GapInt'] == 500   # 72500 - 72000
    
    def test_quali_gaps_use_fastest_lap(self):
        """Test that quali gaps use FastestLapTimeInt."""
        drivers = [
            {'Position': 1, 'Name': 'P1', 'TimeInt': 80000, 'FastestLapTimeInt': 72000},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 80500, 'FastestLapTimeInt': 72200}
        ]
        
        result = _calculate_gaps_quali(drivers)
        
        # Should use FastestLapTimeInt, not TimeInt
        assert result[0]['GapInt'] == 0
        assert result[1]['GapInt'] == 200  # 72200 - 72000, NOT 80500 - 80000
    
    def test_quali_gaps_never_negative(self):
        """Test that quali gaps are never negative."""
        drivers = [
            {'Position': 1, 'Name': 'P1', 'TimeInt': 72000, 'FastestLapTimeInt': 72000},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 71000, 'FastestLapTimeInt': 71000}  # Invalid: faster than pole
        ]
        
        result = _calculate_gaps_quali(drivers)
        
        # Gap should be clamped to 0, not negative
        assert result[1]['GapInt'] >= 0
    
    def test_gaps_sorting(self):
        """Test that drivers are sorted by position."""
        drivers = [
            {'Position': 3, 'Name': 'P3', 'TimeInt': 91500, 'Laps': 50, 'FastestLapTimeInt': 1820},
            {'Position': 1, 'Name': 'P1', 'TimeInt': 90000, 'Laps': 50, 'FastestLapTimeInt': 1800},
            {'Position': 2, 'Name': 'P2', 'TimeInt': 91000, 'Laps': 50, 'FastestLapTimeInt': 1810}
        ]
        
        result = _calculate_gaps_race(drivers)
        
        # Should be sorted by Position
        assert result[0]['Position'] == 1
        assert result[1]['Position'] == 2
        assert result[2]['Position'] == 3
    
    def test_empty_drivers_list(self):
        """Test that empty drivers list is handled."""
        result = _calculate_gaps_race([])
        assert result == []
        
        result = _calculate_gaps_quali([])
        assert result == []
