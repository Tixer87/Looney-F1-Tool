"""Tests for StintsRaw encoder."""

import pytest
from export.rlt_adapter import encode_stints_raw


class TestStintsEncoder:
    """Test stints encoding to RLT StintsRaw format."""
    
    def test_single_stint(self):
        """Test encoding single stint."""
        stints = [
            {'tyre_type': 'Soft', 'laps': 25, 'wear_start': 100, 'wear_end': 35}
        ]
        
        result = encode_stints_raw(stints)
        
        # Format: tyre:laps:wear_start:wear_end
        # Soft = 0 (check rlt_enums.py for actual mapping)
        assert ':' in result
        assert result.startswith('0:25:100:35') or result.startswith('11:25:100:35')  # Soft could be 0 or C5 (11)
    
    def test_multiple_stints(self):
        """Test encoding multiple stints."""
        stints = [
            {'tyre_type': 'Soft', 'laps': 25, 'wear_start': 100, 'wear_end': 35},
            {'tyre_type': 'Medium', 'laps': 30, 'wear_start': 100, 'wear_end': 20},
            {'tyre_type': 'Hard', 'laps': 23, 'wear_start': 100, 'wear_end': 15}
        ]
        
        result = encode_stints_raw(stints)
        
        # Should be comma-separated
        assert ',' in result
        parts = result.split(',')
        assert len(parts) == 3
    
    def test_stint_without_wear(self):
        """Test encoding stint without wear data."""
        stints = [
            {'tyre_type': 'Soft', 'laps': 25}
        ]
        
        result = encode_stints_raw(stints)
        
        # Format: tyre:laps:: (empty wear fields)
        assert result.endswith('::') or '::' in result
    
    def test_stint_with_partial_wear(self):
        """Test encoding stint with only wear_start."""
        stints = [
            {'tyre_type': 'Soft', 'laps': 25, 'wear_start': 100}
        ]
        
        result = encode_stints_raw(stints)
        
        # Should have wear_start but empty wear_end
        parts = result.split(':')
        assert len(parts) == 4
        assert parts[2] == '100'
        assert parts[3] == ''
    
    def test_empty_stints(self):
        """Test encoding empty stints list."""
        result = encode_stints_raw([])
        assert result == ''
    
    def test_tyre_type_numeric(self):
        """Test that tyre types are converted to numeric."""
        stints = [
            {'tyre_type': 'Soft', 'laps': 25}
        ]
        
        result = encode_stints_raw(stints)
        
        # Should start with a number (tyre type)
        first_part = result.split(':')[0]
        assert first_part.isdigit()
    
    def test_tyre_type_already_numeric(self):
        """Test that numeric tyre types are preserved."""
        stints = [
            {'tyre_type': 0, 'laps': 25}  # Already numeric
        ]
        
        result = encode_stints_raw(stints)
        
        assert result.startswith('0:')
    
    def test_all_standard_tyre_types(self):
        """Test all standard F1 tyre types."""
        tyre_types = ['Soft', 'Medium', 'Hard', 'Intermediate', 'Wet']
        
        for tyre in tyre_types:
            stints = [{'tyre_type': tyre, 'laps': 10}]
            result = encode_stints_raw(stints)
            
            assert result != '', f"Failed to encode {tyre}"
            assert ':' in result
    
    def test_c_compound_tyre_types(self):
        """Test C1-C6 compound tyre types."""
        for i in range(1, 7):
            compound = f'C{i}'
            stints = [{'tyre_type': compound, 'laps': 10}]
            result = encode_stints_raw(stints)
            
            assert result != '', f"Failed to encode {compound}"
            assert ':' in result
    
    def test_invalid_tyre_type_skipped(self, caplog):
        """Test that invalid tyre types are skipped with warning."""
        stints = [
            {'tyre_type': 'InvalidTyre', 'laps': 25}
        ]
        
        result = encode_stints_raw(stints)
        
        # Should return empty string (invalid tyre type is skipped)
        assert result == ''
    
    def test_zero_laps(self):
        """Test stint with zero laps."""
        stints = [
            {'tyre_type': 'Soft', 'laps': 0}
        ]
        
        result = encode_stints_raw(stints)
        
        # Should encode with 0 laps
        assert ':0:' in result
    
    def test_wear_bounds(self):
        """Test wear values are integers."""
        stints = [
            {'tyre_type': 'Soft', 'laps': 25, 'wear_start': 100, 'wear_end': 0}
        ]
        
        result = encode_stints_raw(stints)
        
        parts = result.split(':')
        assert parts[2] == '100'
        assert parts[3] == '0'
    
    def test_alternative_field_names(self):
        """Test that alternative field names (capitalized) work."""
        stints = [
            {'TyreType': 'Soft', 'Laps': 25, 'WearStart': 100, 'WearEnd': 35}
        ]
        
        result = encode_stints_raw(stints)
        
        # Should handle capitalized field names
        assert result != ''
        assert ':' in result
    
    def test_format_regex_compliance(self):
        """Test that output matches StintsRaw regex pattern."""
        import re
        
        stints = [
            {'tyre_type': 'Soft', 'laps': 25, 'wear_start': 100, 'wear_end': 35},
            {'tyre_type': 'Medium', 'laps': 30}
        ]
        
        result = encode_stints_raw(stints)
        
        # RLT spec regex: ^(\d+:\d+:(?:\d+)?:(?:\d+)?(?:,\d+:\d+:(?:\d+)?:(?:\d+)?)*)?$
        pattern = r'^(\d+:\d+:(?:\d+)?:(?:\d+)?(?:,\d+:\d+:(?:\d+)?:(?:\d+)?)*)?$'
        
        assert re.match(pattern, result), f"StintsRaw does not match pattern: {result}"
