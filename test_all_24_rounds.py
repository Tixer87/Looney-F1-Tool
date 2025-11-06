#!/usr/bin/env python3
"""
Comprehensive test: All 24 rounds of 2025 F1 season.
Validates circuit mapping and qualifying export for every race.
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, '.')
from api.export_service import run_export

# 2025 F1 Calendar (24 Rounds)
# Note: Rounds 21-24 not yet raced in 2025, fallback to 2024 for testing
CALENDAR_2025 = [
    (1, "Australia", "Melbourne", "🇦🇺", 2025),
    (2, "China", "Shanghai", "🇨🇳", 2025),
    (3, "Japan", "Suzuka", "🇯🇵", 2025),
    (4, "Bahrain", "Sakhir", "🇧🇭", 2025),
    (5, "Saudi Arabia", "Jeddah", "🇸🇦", 2025),
    (6, "Miami", "Miami", "🇺🇸", 2025),
    (7, "Emilia Romagna", "Imola", "🇮🇹", 2025),
    (8, "Monaco", "Monaco", "🇲🇨", 2025),
    (9, "Spain", "Barcelona", "🇪🇸", 2025),
    (10, "Canada", "Montreal", "🇨🇦", 2025),
    (11, "Austria", "Spielberg", "🇦🇹", 2025),
    (12, "Great Britain", "Silverstone", "🇬🇧", 2025),
    (13, "Belgium", "Spa-Francorchamps", "🇧🇪", 2025),
    (14, "Hungary", "Hungaroring", "🇭🇺", 2025),
    (15, "Netherlands", "Zandvoort", "🇳🇱", 2025),
    (16, "Italy", "Monza", "🇮🇹", 2025),
    (17, "Azerbaijan", "Baku", "🇦🇿", 2025),
    (18, "Singapore", "Singapore", "🇸🇬", 2025),
    (19, "United States", "Austin", "🇺🇸", 2025),
    (20, "Mexico", "Mexico City", "🇲🇽", 2025),
    (21, "Brazil", "Interlagos", "🇧🇷", 2024),  # 2025 not yet raced
    (22, "Las Vegas", "Las Vegas", "🇺🇸", 2024),  # 2025 not yet raced
    (23, "Qatar", "Losail", "🇶🇦", 2024),  # 2025 not yet raced
    (24, "Abu Dhabi", "Yas Marina", "🇦🇪", 2024),  # 2025 not yet raced
]

def test_round(round_no: int, country: str, circuit: str, flag: str, season: int = 2025):
    """Test qualifying export for a single round."""
    season_label = f" [{season}]" if season != 2025 else ""
    print(f"\n{flag} R{round_no:02d} {country} ({circuit}){season_label}")
    print("─" * 60)
    
    try:
        # Export qualifying (will split into Q1/Q2/Q3)
        start_time = time.time()
        result = run_export(
            season=season,
            round_no=round_no,
            session='Q',
            out_dir=Path('./test_all_rounds'),
            verbose=False
        )
        elapsed = time.time() - start_time
        
        if result:
            # Check if files exist
            q1_file = result.parent / result.name.replace('_Q3.json', '_Q1.json')
            q2_file = result.parent / result.name.replace('_Q3.json', '_Q2.json')
            q3_file = result
            
            if q1_file.exists() and q2_file.exists() and q3_file.exists():
                # Read Q3 to get details
                import json
                q3_data = json.loads(q3_file.read_text())
                
                print(f"✅ SUCCESS ({elapsed:.1f}s)")
                print(f"   Track: {q3_data['TrackName']} ({q3_data['TrackUniqueName']})")
                print(f"   Files: Q1 ✓ Q2 ✓ Q3 ✓")
                print(f"   Q3 Drivers: {len(q3_data['Drivers'])}")
                if len(q3_data['Drivers']) > 0:
                    pole = q3_data['Drivers'][0]
                    print(f"   Pole: {pole['Driver']['Name']} (P{pole['Position']})")
                return True
            else:
                print(f"❌ FAILED: Missing files")
                return False
        else:
            print(f"❌ FAILED: Export returned None")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)[:100]}")
        return False

def main():
    """Run comprehensive test for all 24 rounds."""
    print("=" * 60)
    print("🏎️  LOONEY F1 TOOL - 2025 SEASON COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"Testing: All 24 rounds with Qualifying export")
    print(f"Purpose: Validate circuit mapping + Q→Q1/Q2/Q3 split")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path('./test_all_rounds')
    output_dir.mkdir(exist_ok=True)
    
    results = []
    successful = 0
    failed = 0
    
    # Test each round
    for round_no, country, circuit, flag, season in CALENDAR_2025:
        success = test_round(round_no, country, circuit, flag, season)
        results.append((round_no, country, circuit, success))
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Rounds: {len(CALENDAR_2025)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(successful/len(CALENDAR_2025)*100):.1f}%")
    
    if failed > 0:
        print("\n❌ Failed Rounds:")
        for round_no, country, circuit, success in results:
            if not success:
                print(f"   R{round_no:02d}: {country} ({circuit})")
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Ready for EXE build.")
    else:
        print("⚠️  Some tests failed. Check circuit mappings.")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
