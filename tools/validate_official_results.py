"""Validate exported results against official data."""

import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    """Load JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def get_driver_names(drivers: list) -> list[str]:
    """Extract driver names from results."""
    return [d["Driver"]["Name"] for d in drivers]


def get_driver_numbers(drivers: list) -> list[int]:
    """Extract driver numbers from results."""
    return [d["RaceNumber"] for d in drivers]


def check_qualifying_segment(path: Path, expected: dict, session_name: str):
    """Validate qualifying segment (Q1/Q2/Q3)."""
    print(f"\n🔍 Validating {session_name}...")
    
    data = load_json(path)
    drivers = data["Drivers"]
    
    # Check count
    actual_count = len(drivers)
    expected_count = expected["count"]
    assert actual_count == expected_count, \
        f"❌ {session_name}: Driver count {actual_count} != {expected_count}"
    print(f"  ✅ Driver count: {actual_count}")
    
    # Check top 3 if specified
    if "top3_drivers" in expected:
        actual_top3 = get_driver_names(drivers)[:3]
        expected_top3 = expected["top3_drivers"]
        assert actual_top3 == expected_top3, \
            f"❌ {session_name}: Top 3 {actual_top3} != {expected_top3}"
        print(f"  ✅ Top 3: {', '.join(actual_top3)}")
    
    # Check top 3 numbers if specified
    if "top3_numbers" in expected:
        actual_numbers = get_driver_numbers(drivers)[:3]
        expected_numbers = expected["top3_numbers"]
        assert actual_numbers == expected_numbers, \
            f"❌ {session_name}: Top 3 numbers {actual_numbers} != {expected_numbers}"
        print(f"  ✅ Top 3 numbers: {actual_numbers}")
    
    # Check pole if specified (Q3)
    if "pole_driver" in expected:
        pole_driver = get_driver_names(drivers)[0]
        expected_pole = expected["pole_driver"]
        assert pole_driver == expected_pole, \
            f"❌ {session_name}: Pole {pole_driver} != {expected_pole}"
        print(f"  ✅ Pole position: {pole_driver} (#{get_driver_numbers(drivers)[0]})")
    
    print(f"  ✅ {session_name} validation passed!")


def check_race(path: Path, expected: dict):
    """Validate race results."""
    print(f"\n🔍 Validating Race...")
    
    data = load_json(path)
    drivers = data["Drivers"]
    
    # Check classified drivers
    actual_count = len(drivers)
    expected_count = expected["classified"]
    assert actual_count >= expected_count, \
        f"❌ Race: Classified {actual_count} < {expected_count}"
    print(f"  ✅ Classified drivers: {actual_count}")
    
    # Check winner
    winner_name = get_driver_names(drivers)[0]
    expected_winner = expected["winner_driver"]
    assert winner_name == expected_winner, \
        f"❌ Race: Winner {winner_name} != {expected_winner}"
    print(f"  ✅ Winner: {winner_name} (#{get_driver_numbers(drivers)[0]})")
    
    # Check top 3
    if "top3_drivers" in expected:
        actual_top3 = get_driver_names(drivers)[:3]
        expected_top3 = expected["top3_drivers"]
        assert actual_top3 == expected_top3, \
            f"❌ Race: Top 3 {actual_top3} != {expected_top3}"
        print(f"  ✅ Top 3: {', '.join(actual_top3)}")
    
    # Check total laps if specified (FastF1 limitation: may return 0)
    if "total_laps" in expected:
        total_laps = data.get("TotalLaps", 0)
        expected_laps = expected["total_laps"]
        if total_laps > 0:
            assert total_laps >= expected_laps - 2, \
                f"❌ Race: Total laps {total_laps} != {expected_laps}"
            print(f"  ✅ Total laps: {total_laps}")
        else:
            print(f"  ⚠️  Total laps: 0 (FastF1 limitation, expected {expected_laps})")
    
    print(f"  ✅ Race validation passed!")


def main():
    """Run validation."""
    print("="*60)
    print("🏁 Official Results Validator - Australia 2025 R1")
    print("="*60)
    
    base_dir = Path(r"C:\Users\ktixe\Documents\LooneyExports\2025_R01_Melbourne")
    official_path = Path(r"official\2025_R01_Australia\event_official.json")
    
    # Load official data
    official = load_json(official_path)
    expectations = official["expect"]
    
    print(f"\n📋 Event: {official['event']}")
    print(f"📁 Export directory: {base_dir}")
    
    try:
        # Validate Q1
        check_qualifying_segment(
            base_dir / "2025_Melbourne_Australia_Q1.json",
            expectations["Q1"],
            "Q1"
        )
        
        # Validate Q2
        check_qualifying_segment(
            base_dir / "2025_Melbourne_Australia_Q2.json",
            expectations["Q2"],
            "Q2"
        )
        
        # Validate Q3
        check_qualifying_segment(
            base_dir / "2025_Melbourne_Australia_Q3.json",
            expectations["Q3"],
            "Q3"
        )
        
        # Validate Race
        check_race(
            base_dir / "2025_Melbourne_Australia_Race.json",
            expectations["Race"]
        )
        
        print("\n" + "="*60)
        print("✅ ALL VALIDATIONS PASSED!")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n{'='*60}")
        print(str(e))
        print("="*60)
        return 1
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Unexpected error: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
