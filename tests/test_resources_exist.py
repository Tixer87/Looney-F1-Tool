import json
from api.export_service import resource_path
from mapping.circuit_aliases import CIRCUITS,get_circuit
from mapping.drivers_nations import get_driver_nation
def test_core_resources_exist():
    config_file=resource_path("config.json")
    assert config_file.exists(),f"Ressource config.json fehlt: {config_file}"
def test_mapping_files_are_valid_json():
    mapping_files=["mapping/driver_alias_map.json","mapping/team_alias_map.json","mapping/nations_alias_map.json"]
    for rel in mapping_files:
        resource_file=resource_path(rel)
        if resource_file.exists():
            with open(resource_file,"r",encoding="utf-8") as f:
                data=json.load(f)
                assert isinstance(data,(dict,list)),f"{rel} sollte JSON dict oder list sein"
def test_circuit_mapping_is_available():
    assert CIRCUITS,"Circuit Mapping ist leer"
    assert len(CIRCUITS)==27,f"27 Circuits erwartet, gefunden: {len(CIRCUITS)}"
    name,unique=get_circuit("Monaco")
    assert name=="Monaco"
    assert unique=="monaco.2015"
def test_nation_mapping_is_available():
    assert get_driver_nation("Dutch")=={"Name":"Netherlands","Code":"NLD"}
    assert get_driver_nation("British")=={"Name":"United Kingdom","Code":"GBR"}
def test_config_file_exists():
    config_file=resource_path("config.json")
    assert config_file.exists(),"config.json fehlt"
    with open(config_file,"r",encoding="utf-8") as f:
        config=json.load(f)
        assert isinstance(config,dict),"config.json sollte ein JSON Objekt sein"