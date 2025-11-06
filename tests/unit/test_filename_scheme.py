# tests/unit/test_filename_scheme.py
"""Tests for the new filename scheme with circuit names"""

from api.export_service import safe_name, build_output_name, unique_path

class TestFileNaming:
    """Test filename generation functions"""
    
    def test_safe_name_basic(self):
        """Test basic safe name conversion"""
        assert safe_name("Autodromo Nazionale Monza") == "Autodromo_Nazionale_Monza"
        assert safe_name("Circuit de Spa-Francorchamps") == "Circuit_de_Spa-Francorchamps"
        assert safe_name("Red Bull Ring") == "Red_Bull_Ring"
        
    def test_safe_name_special_chars(self):
        """Test safe name with special characters"""
        assert safe_name("Circuit Gilles Villeneuve (Montréal)") == "Circuit_Gilles_Villeneuve_Montral"
        assert safe_name("Hungaroring: Hungarian GP") == "Hungaroring_Hungarian_GP"
        assert safe_name("Street Circuit!@#$%") == "Street_Circuit"
        
    def test_safe_name_whitespace(self):
        """Test safe name with multiple spaces and tabs"""
        assert safe_name("  Marina Bay   Street Circuit  ") == "Marina_Bay_Street_Circuit"
        assert safe_name("Circuit\t\nde Monaco") == "Circuit_de_Monaco"
        
    def test_build_output_name_qualifying(self):
        """Test qualifying filename generation"""
        event = {"Circuit": {"circuitName": "Autodromo Nazionale Monza"}}
        
        # With quali phase
        result = build_output_name(2025, 16, "Q", "Q3", event)
        assert result == "2025_Autodromo_Nazionale_Monza_Qualifying_Q3.json"
        
        result = build_output_name(2025, 16, "Q", "Q1", event)
        assert result == "2025_Autodromo_Nazionale_Monza_Qualifying_Q1.json"
        
        # Without quali phase
        result = build_output_name(2025, 16, "Q", None, event)
        assert result == "2025_Autodromo_Nazionale_Monza_Qualifying.json"
        
    def test_build_output_name_other_sessions(self):
        """Test other session types"""
        event = {"Circuit": {"circuitName": "Circuit de Spa-Francorchamps"}}
        
        # Race
        result = build_output_name(2025, 14, "R", None, event)
        assert result == "2025_Circuit_de_Spa-Francorchamps_Race.json"
        
        # Sprint
        result = build_output_name(2025, 14, "SQ", None, event)
        assert result == "2025_Circuit_de_Spa-Francorchamps_Sprint.json"
        
        # Practice
        result = build_output_name(2025, 14, "P", None, event)
        assert result == "2025_Circuit_de_Spa-Francorchamps_Practice.json"
        
    def test_build_output_name_fallback(self):
        """Test filename with fallback when circuit name missing"""
        # Empty event
        event = {}
        result = build_output_name(2025, 5, "R", None, event)
        assert result == "2025_Round_5_Race.json"
        
        # Event with race name but no circuit
        event = {"raceName": "Monaco Grand Prix"}
        result = build_output_name(2025, 8, "Q", None, event)
        assert result == "2025_Monaco_Grand_Prix_Qualifying.json"
        
    def test_build_output_name_alternative_circuit_keys(self):
        """Test different ways circuit name can be stored"""
        # Direct circuitName
        event = {"circuitName": "Silverstone Circuit"}
        result = build_output_name(2025, 10, "R", None, event)
        assert result == "2025_Silverstone_Circuit_Race.json"
        
        # Race name fallback
        event = {"raceName": "British Grand Prix"}  
        result = build_output_name(2025, 10, "R", None, event)
        assert result == "2025_British_Grand_Prix_Race.json"

class TestUniquePathGeneration:
    """Test unique path generation to avoid collisions"""
    
    def test_unique_path_no_collision(self, tmp_path):
        """Test when no collision occurs"""
        filename = "2025_Monza_Race.json"
        result = unique_path(tmp_path, filename)
        
        assert result == tmp_path / filename
        assert not result.exists()  # File should not exist yet
        
    def test_unique_path_with_collision(self, tmp_path):
        """Test collision resolution"""
        filename = "2025_Monza_Race.json"
        
        # Create existing file
        existing = tmp_path / filename
        existing.touch()
        
        # Generate unique path
        result = unique_path(tmp_path, filename)
        
        assert result == tmp_path / "2025_Monza_Race_02.json"
        assert not result.exists()  # New file should not exist
        assert existing.exists()    # Original should still exist
        
    def test_unique_path_multiple_collisions(self, tmp_path):
        """Test multiple collision resolution"""
        filename = "2025_Monza_Race.json"
        
        # Create multiple existing files
        (tmp_path / filename).touch()
        (tmp_path / "2025_Monza_Race_02.json").touch()
        (tmp_path / "2025_Monza_Race_03.json").touch()
        
        # Generate unique path
        result = unique_path(tmp_path, filename)
        
        assert result == tmp_path / "2025_Monza_Race_04.json"
        assert not result.exists()
        
    def test_unique_path_preserves_extension(self, tmp_path):
        """Test that file extension is preserved"""
        filename = "test_file.csv"
        
        # Create existing file
        (tmp_path / filename).touch()
        
        result = unique_path(tmp_path, filename)
        
        assert result == tmp_path / "test_file_02.csv"
        assert result.suffix == ".csv"