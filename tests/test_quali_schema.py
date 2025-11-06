"""Qualification Schema Regression Tests - Golden Fixture Validation

Tests RLT qualification exports against golden fixtures to prevent regressions.
Validates:
- All required top-level fields present
- Q1 field present for all drivers (MANDATORY for quali)
- Status="Ok" for all drivers (quali requirement)
- Zero "Unknown" entries in teams/nationalities

Golden Fixture: tests/fixtures/mexico_2025_quali.json
"""

import json
import pytest
from pathlib import Path

# Mark all tests in this module as golden fixture tests (no coverage required)
pytestmark = pytest.mark.golden


@pytest.fixture
def golden_quali():
    """Load golden qualification fixture (Mexico 2025)."""
    fixture_path = Path(__file__).parent / "fixtures" / "mexico_2025_quali.json"
    if not fixture_path.exists():
        pytest.skip(f"Golden fixture not found: {fixture_path}")
    
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def test_quali_top_level_required_fields(golden_quali):
    """Test that all required top-level fields are present."""
    required = [
        "SessionType", "RaceType", "QualType", "SessionStatus",
        "SessionPosition", "Date", "TrackName", "TrackUniqueName",
        "IsLiveData", "LiveRecordPercent", "IsLiveFullRecord", "IsSingleplayerMode",
        "WeatherType", "AirTemperature", "TrackTemperature",
        "TotalLaps", "SessionDuration", "Drivers"
    ]
    
    missing = [field for field in required if field not in golden_quali]
    assert not missing, f"Missing required top-level fields: {missing}"


def test_quali_session_type(golden_quali):
    """Test that SessionType is Qualification."""
    assert golden_quali["SessionType"] == "Qualification"


def test_quali_has_qual_type(golden_quali):
    """Test that QualType field exists for qualification sessions."""
    assert "QualType" in golden_quali
    assert golden_quali["QualType"] in ["Regular", "Q1", "Q2", "Q3", "Q4"]


def test_quali_fastest_lap_driver_object(golden_quali):
    """Test that FastestLapDriver object is present and valid."""
    assert "FastestLapDriver" in golden_quali
    
    if golden_quali["FastestLapDriver"]:  # Can be null if no laps completed
        flap = golden_quali["FastestLapDriver"]
        assert "Name" in flap, "FastestLapDriver missing 'Name' field"
        assert "Nationality" in flap, "FastestLapDriver missing 'Nationality' field"
        assert isinstance(flap["Name"], str), "FastestLapDriver Name must be string"
        assert isinstance(flap["Nationality"], str), "FastestLapDriver Nationality must be string"


def test_quali_drivers_present(golden_quali):
    """Test that drivers list is not empty."""
    assert "Drivers" in golden_quali
    drivers = golden_quali["Drivers"]
    assert isinstance(drivers, list), "Drivers must be a list"
    assert len(drivers) > 0, "Drivers list must not be empty"


def test_quali_driver_required_fields(golden_quali):
    """Test that all drivers have required fields."""
    required = [
        "Driver", "Position", "Team", "SeatType", "Status",
        "TimeInt", "GapInt", "LapsCount", "GridPosition", "PitsCount"
    ]
    
    drivers = golden_quali["Drivers"]
    for i, driver in enumerate(drivers, 1):
        missing = [field for field in required if field not in driver]
        assert not missing, f"Driver {i} missing required fields: {missing}"


def test_quali_driver_q1_mandatory(golden_quali):
    """Test that all drivers have Q1 field (MANDATORY for qualification)."""
    drivers = golden_quali["Drivers"]
    
    for i, driver in enumerate(drivers, 1):
        driver_name = driver.get("Driver", {}).get("Name", f"Driver {i}")
        
        # Q1 field must exist
        assert "Q1" in driver, f"Driver {i} ({driver_name}) missing Q1 field (MANDATORY for quali)"
        
        # Q1 must be a string in format "m:ss.mmm"
        q1 = driver["Q1"]
        assert isinstance(q1, str), f"Driver {i} ({driver_name}) Q1 must be string, got {type(q1).__name__}"
        assert ":" in q1, f"Driver {i} ({driver_name}) Q1 format invalid: '{q1}' (expected 'm:ss.mmm')"
        assert "." in q1, f"Driver {i} ({driver_name}) Q1 format invalid: '{q1}' (expected 'm:ss.mmm')"


def test_quali_driver_q1_format_valid(golden_quali):
    """Test that Q1 times are in valid format 'm:ss.mmm'."""
    drivers = golden_quali["Drivers"]
    
    for i, driver in enumerate(drivers, 1):
        driver_name = driver.get("Driver", {}).get("Name", f"Driver {i}")
        q1 = driver["Q1"]
        
        # Parse Q1 format
        try:
            parts = q1.split(":")
            assert len(parts) == 2, "Must have format 'm:ss.mmm'"
            
            minutes = int(parts[0])
            seconds_parts = parts[1].split(".")
            assert len(seconds_parts) == 2, "Must have format 'm:ss.mmm'"
            
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1])
            
            assert 0 <= minutes < 60, f"Minutes must be 0-59, got {minutes}"
            assert 0 <= seconds < 60, f"Seconds must be 0-59, got {seconds}"
            assert 0 <= milliseconds < 1000, f"Milliseconds must be 0-999, got {milliseconds}"
            
        except (ValueError, AssertionError) as e:
            pytest.fail(f"Driver {i} ({driver_name}) Q1 format invalid: '{q1}' - {e}")


def test_quali_driver_status_ok(golden_quali):
    """Test that all drivers have Status='Ok' for qualification sessions."""
    drivers = golden_quali["Drivers"]
    
    for i, driver in enumerate(drivers, 1):
        driver_name = driver.get("Driver", {}).get("Name", f"Driver {i}")
        status = driver.get("Status")
        
        assert status == "Ok", (
            f"Driver {i} ({driver_name}) Status='{status}' "
            f"(must be 'Ok' for qualification sessions)"
        )


def test_quali_driver_nested_objects(golden_quali):
    """Test that Driver and Team nested objects have required fields."""
    drivers = golden_quali["Drivers"]
    
    for i, driver in enumerate(drivers, 1):
        # Driver object
        assert "Driver" in driver, f"Driver {i} missing 'Driver' object"
        driver_obj = driver["Driver"]
        assert "Name" in driver_obj, f"Driver {i} Driver object missing 'Name'"
        assert "Nationality" in driver_obj, f"Driver {i} Driver object missing 'Nationality'"
        
        # Team object
        assert "Team" in driver, f"Driver {i} missing 'Team' object"
        team_obj = driver["Team"]
        assert "Name" in team_obj, f"Driver {i} Team object missing 'Name'"
        assert "UniqueName" in team_obj, f"Driver {i} Team object missing 'UniqueName'"


def test_quali_zero_unknown_teams(golden_quali):
    """Test that no drivers have 'Unknown Team' (Phase C++ H1 requirement)."""
    drivers = golden_quali["Drivers"]
    
    unknown_teams = [
        (i, driver.get("Driver", {}).get("Name", f"Driver {i}"))
        for i, driver in enumerate(drivers, 1)
        if "Unknown" in driver.get("Team", {}).get("Name", "")
    ]
    
    assert not unknown_teams, (
        f"Found {len(unknown_teams)} drivers with 'Unknown Team': "
        f"{', '.join(f'{name} (pos {pos})' for pos, name in unknown_teams)}"
    )


def test_quali_zero_unknown_nationalities(golden_quali):
    """Test that no drivers have 'Unknown' nationality (Phase C++ H1 requirement)."""
    drivers = golden_quali["Drivers"]
    
    unknown_nations = [
        (i, driver.get("Driver", {}).get("Name", f"Driver {i}"))
        for i, driver in enumerate(drivers, 1)
        if driver.get("Driver", {}).get("Nationality", "").lower() in ["unknown", "unk"]
    ]
    
    assert not unknown_nations, (
        f"Found {len(unknown_nations)} drivers with 'Unknown' nationality: "
        f"{', '.join(f'{name} (pos {pos})' for pos, name in unknown_nations)}"
    )


def test_quali_time_int_populated(golden_quali):
    """Test that TimeInt is populated (not 0) for drivers with lap times."""
    drivers = golden_quali["Drivers"]
    
    # For drivers with Q1 times > 0, TimeInt should also be > 0
    invalid = []
    for i, driver in enumerate(drivers, 1):
        driver_name = driver.get("Driver", {}).get("Name", f"Driver {i}")
        q1 = driver.get("Q1", "0:00.000")
        time_int = driver.get("TimeInt", 0)
        
        # If Q1 is not "0:00.000", TimeInt should be > 0
        if q1 != "0:00.000" and time_int == 0:
            invalid.append((i, driver_name, q1))
    
    assert not invalid, (
        f"Found {len(invalid)} drivers with Q1 time but TimeInt=0: "
        f"{', '.join(f'{name} (pos {pos}, Q1={q1})' for pos, name, q1 in invalid)}"
    )


def test_quali_gap_calculation(golden_quali):
    """Test that gaps are calculated correctly (Quali: gap to pole)."""
    drivers = golden_quali["Drivers"]
    
    # Sort by position
    sorted_drivers = sorted(drivers, key=lambda d: d.get("Position", 999))
    
    if not sorted_drivers:
        pytest.skip("No drivers to test")
    
    # Pole position (P1) should have GapInt=0
    pole = sorted_drivers[0]
    assert pole.get("Position") == 1, "First driver in sorted list should be P1"
    assert pole.get("GapInt", -1) == 0, f"Pole position driver should have GapInt=0, got {pole.get('GapInt')}"


@pytest.mark.parametrize("field,expected_type", [
    ("SessionStatus", str),
    ("LiveRecordPercent", int),
    ("IsLiveFullRecord", bool),
    ("IsSingleplayerMode", bool),
    ("WeatherType", str),
    ("AirTemperature", int),
    ("TrackTemperature", int),
    ("SessionDuration", str),
    ("TotalLaps", int),
])
def test_quali_field_types(golden_quali, field, expected_type):
    """Test that required fields have correct data types."""
    assert field in golden_quali, f"Field '{field}' missing from document"
    value = golden_quali[field]
    assert isinstance(value, expected_type), (
        f"Field '{field}' should be {expected_type.__name__}, "
        f"got {type(value).__name__}: {value}"
    )
