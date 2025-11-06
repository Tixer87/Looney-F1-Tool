# tests/test_resources_exist.py
from api.export_service import resource_path

def test_core_resources_exist():
    """Test dass alle notwendigen Ressourcen-Dateien existieren"""
    required_resources = [
        "mapping/teams.f1.json", 
        "mapping/circuits.json", 
        "mapping/drivers.json", 
        "config.json"
    ]
    
    for rel in required_resources:
        resource_file = resource_path(rel)
        assert resource_file.exists(), f"Ressource {rel} fehlt: {resource_file}"
        
def test_mapping_files_are_valid_json():
    """Test dass alle Mapping-Dateien gültiges JSON enthalten"""
    mapping_files = [
        "mapping/teams.f1.json",
        "mapping/circuits.json", 
        "mapping/drivers.json",
        "mapping/cars.f1.json",
        "mapping/championships.json",
        "mapping/lineups.f1.json",
        "mapping/nations.json"
    ]
    
    for rel in mapping_files:
        resource_file = resource_path(rel)
        if resource_file.exists():  # Optional files
            # Test if file contains valid JSON
            import json
            with open(resource_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert isinstance(data, (dict, list)), f"{rel} sollte JSON dict oder list sein"

def test_config_file_exists():
    """Test dass config.json existiert und gültig ist"""
    config_file = resource_path("config.json")
    assert config_file.exists(), "config.json fehlt"
    
    import json
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
        assert isinstance(config, dict), "config.json sollte ein JSON-Objekt sein"
