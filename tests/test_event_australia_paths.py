"""Test exported files for Australia 2025 R1."""

from pathlib import Path
import pytest


@pytest.fixture
def export_dir():
    """Export directory fixture."""
    return Path(r"C:\Users\ktixe\Documents\LooneyExports\2025_R01_Melbourne")


def test_export_outputs_exist(export_dir):
    """Verify all expected export files exist."""
    # Practice sessions
    assert (export_dir / "2025_Melbourne_Australia_FP1.json").exists(), "FP1 missing"
    assert (export_dir / "2025_Melbourne_Australia_FP2.json").exists(), "FP2 missing"
    assert (export_dir / "2025_Melbourne_Australia_FP3.json").exists(), "FP3 missing"
    
    # Qualifying split
    assert (export_dir / "2025_Melbourne_Australia_Q1.json").exists(), "Q1 missing"
    assert (export_dir / "2025_Melbourne_Australia_Q2.json").exists(), "Q2 missing"
    assert (export_dir / "2025_Melbourne_Australia_Q3.json").exists(), "Q3 missing"
    
    # Race
    assert (export_dir / "2025_Melbourne_Australia_Race.json").exists(), "Race missing"


def test_file_sizes(export_dir):
    """Verify files are not empty."""
    files = [
        "2025_Melbourne_Australia_FP1.json",
        "2025_Melbourne_Australia_FP2.json",
        "2025_Melbourne_Australia_FP3.json",
        "2025_Melbourne_Australia_Q1.json",
        "2025_Melbourne_Australia_Q2.json",
        "2025_Melbourne_Australia_Q3.json",
        "2025_Melbourne_Australia_Race.json",
    ]
    
    for filename in files:
        filepath = export_dir / filename
        assert filepath.stat().st_size > 500, f"{filename} is too small (< 500 bytes)"


def test_qualifying_driver_counts(export_dir):
    """Verify correct driver counts in qualifying segments."""
    import json
    
    q1 = json.loads((export_dir / "2025_Melbourne_Australia_Q1.json").read_text())
    q2 = json.loads((export_dir / "2025_Melbourne_Australia_Q2.json").read_text())
    q3 = json.loads((export_dir / "2025_Melbourne_Australia_Q3.json").read_text())
    
    assert len(q1["Drivers"]) == 19, f"Q1 should have 19 drivers, got {len(q1['Drivers'])}"
    assert len(q2["Drivers"]) == 15, f"Q2 should have 15 drivers, got {len(q2['Drivers'])}"
    assert len(q3["Drivers"]) == 10, f"Q3 should have 10 drivers, got {len(q3['Drivers'])}"


def test_race_winner(export_dir):
    """Verify race winner."""
    import json
    
    race = json.loads((export_dir / "2025_Melbourne_Australia_Race.json").read_text())
    winner = race["Drivers"][0]
    
    assert winner["Position"] == 1, "Winner should be position 1"
    assert winner["Driver"]["Name"] == "Lando Norris", f"Expected Norris, got {winner['Driver']['Name']}"
    assert winner["RaceNumber"] == 4, f"Expected #4, got #{winner['RaceNumber']}"
