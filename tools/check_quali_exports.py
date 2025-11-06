"""Check qualifying export JSON files for RLT compliance."""

import json
import sys
from pathlib import Path


def check_quali_file(path: Path) -> dict:
    """Check single qualifying export file."""
    print(f"\n{'='*60}")
    print(f"📋 Checking: {path.name}")
    print(f"{'='*60}")
    
    data = json.loads(path.read_text(encoding="utf-8"))
    issues = []
    
    # Session metadata
    session_type = data.get("SessionType")
    qual_type = data.get("QualType")
    drivers = data.get("Drivers", [])
    
    print(f"  SessionType: {session_type}")
    print(f"  QualType: {qual_type}")
    print(f"  Drivers: {len(drivers)}")
    
    if session_type != "Qualification":
        issues.append(f"SessionType should be 'Qualification', got '{session_type}'")
    
    # Check each driver
    for idx, driver in enumerate(drivers, 1):
        # Required fields
        if "Driver" not in driver or "Name" not in driver["Driver"]:
            issues.append(f"Driver {idx}: Missing Driver.Name")
        
        if "RaceNumber" not in driver:
            issues.append(f"Driver {idx}: Missing RaceNumber")
        
        if "Team" not in driver or "Name" not in driver["Team"]:
            issues.append(f"Driver {idx}: Missing Team.Name")
        
        # Time fields
        if "TimeInt" not in driver:
            issues.append(f"Driver {idx}: Missing TimeInt")
        elif not isinstance(driver["TimeInt"], int):
            issues.append(f"Driver {idx}: TimeInt must be integer, got {type(driver['TimeInt'])}")
        
        # Position
        if "Position" not in driver:
            issues.append(f"Driver {idx}: Missing Position")
        elif driver["Position"] != idx:
            issues.append(f"Driver {idx}: Position mismatch (expected {idx}, got {driver['Position']})")
        
        # Team mapping check
        team_name = driver.get("Team", {}).get("Name", "")
        if team_name:
            # Check for common mapping issues
            if "Red Bull Racing" in team_name and "Racing Bulls" in team_name:
                issues.append(f"Driver {idx}: Suspicious team name '{team_name}' - Red Bull vs Racing Bulls confusion?")
            
            print(f"  [{idx:2d}] {driver['Driver']['Name']:20s} #{driver['RaceNumber']:2d} {team_name:20s} {driver['TimeInt']:6d}ms")
    
    # Summary
    if issues:
        print(f"\n❌ Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        return {"status": "FAIL", "issues": issues}
    else:
        print(f"\n✅ All checks passed!")
        return {"status": "PASS", "issues": []}


def main():
    """Check all provided qualifying files."""
    if len(sys.argv) < 2:
        print("Usage: python check_quali_exports.py <Q1.json> <Q2.json> <Q3.json>")
        return 1
    
    print("="*60)
    print("🔍 RLT Qualifying Export Checker")
    print("="*60)
    
    results = {}
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if not path.exists():
            print(f"\n❌ File not found: {filepath}")
            results[path.name] = {"status": "MISSING", "issues": ["File not found"]}
            continue
        
        results[path.name] = check_quali_file(path)
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    total = len(results)
    
    for filename, result in results.items():
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {filename}: {result['status']}")
    
    print(f"\nResult: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All qualifying exports are RLT-ready!")
        return 0
    else:
        print("\n⚠️ Some issues found - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
