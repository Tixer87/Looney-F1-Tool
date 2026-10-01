"""Test exported files for Australia 2025 R1."""

from pathlib import Path
import os
import pytest


@pytest.fixture
def export_dir():
    """Export directory fixture."""
    folder = os.environ.get('LOONEY_TEST_EXPORT_DIR')
    if not folder:
        pytest.skip('Set LOONEY_TEST_EXPORT_DIR to a verified Australia 2025 export')
    return Path(folder)


def test_export_outputs_exist(export_dir):
    """Verify all expected export files exist."""
    # Practice sessions
    assert (export_dir / "2025_Melbourne_FP1.json").exists(), "FP1 missing"
    assert (export_dir / "2025_Melbourne_FP2.json").exists(), "FP2 missing"
    assert (export_dir / "2025_Melbourne_FP3.json").exists(), "FP3 missing"
    
    # Qualifying split
    assert (export_dir / "2025_Melbourne_Q1.json").exists(), "Q1 missing"
    assert (export_dir / "2025_Melbourne_Q2.json").exists(), "Q2 missing"
    assert (export_dir / "2025_Melbourne_Q3.json").exists(), "Q3 missing"
    
    # Race
    assert (export_dir / "2025_Melbourne_Race.json").exists(), "Race missing"


def test_file_sizes(export_dir):
    """Verify files are not empty."""
    files = [
        "2025_Melbourne_FP1.json",
        "2025_Melbourne_FP2.json",
        "2025_Melbourne_FP3.json",
        "2025_Melbourne_Q1.json",
        "2025_Melbourne_Q2.json",
        "2025_Melbourne_Q3.json",
        "2025_Melbourne_Race.json",
    ]
    
    for filename in files:
        filepath = export_dir / filename
        assert filepath.stat().st_size > 500, f"{filename} is too small (< 500 bytes)"


def test_qualifying_driver_counts(export_dir):
    """Verify correct driver counts in qualifying segments."""
    import json
    
    q1 = json.loads((export_dir / "2025_Melbourne_Q1.json").read_text())
    q2 = json.loads((export_dir / "2025_Melbourne_Q2.json").read_text())
    q3 = json.loads((export_dir / "2025_Melbourne_Q3.json").read_text())
    
    assert len(q1["session"]["drivers"]) == 19, f"Q1 should have 19 drivers, got {len(q1['session']['drivers'])}"
    assert len(q2["session"]["drivers"]) == 15, f"Q2 should have 15 drivers, got {len(q2['session']['drivers'])}"
    assert len(q3["session"]["drivers"]) == 10, f"Q3 should have 10 drivers, got {len(q3['session']['drivers'])}"


def test_race_winner(export_dir):
    """Verify race winner."""
    import json
    
    race = json.loads((export_dir / "2025_Melbourne_Race.json").read_text())
    winner = race["session"]["drivers"][0]
    
    assert winner["position"] == 1, "Winner should be position 1"
    assert winner["driverName"] == "Lando Norris", f"Expected Norris, got {winner['driverName']}"
    assert winner["driverInfo"]["raceNumber"] == "4", f"Expected #4, got #{winner['driverInfo']['raceNumber']}"
