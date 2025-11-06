"""Test script for qualifying export with FastF1 split mode."""

import sys
from pathlib import Path
from api.export_service import run_export

def test_qualifying_export():
    """Test Q export for 2025 Melbourne (Round 1)."""
    
    print("=" * 60)
    print("Testing Qualifying Export - 2025 Melbourne (Round 1)")
    print("=" * 60)
    
    # Test parameters
    season = 2025
    round_no = 1
    session = 'Q'
    out_dir = Path('rlt-ready/test_quali')
    
    print(f"\nParameters:")
    print(f"  Season: {season}")
    print(f"  Round: {round_no}")
    print(f"  Session: {session}")
    print(f"  Output: {out_dir}")
    print()
    
    # Run export
    try:
        result = run_export(
            season=season,
            round_no=round_no,
            session=session,
            out_dir=out_dir,
            verbose=True
        )
        
        print()
        print("=" * 60)
        if result:
            print("✅ Export successful!")
            print(f"Last file: {result}")
            
            # List all files created
            if out_dir.exists():
                files = sorted(out_dir.glob("*.json"))
                print(f"\nCreated {len(files)} file(s):")
                for f in files:
                    size_kb = f.stat().st_size / 1024
                    print(f"  📄 {f.name} ({size_kb:.1f} KB)")
        else:
            print("❌ Export failed - no data available")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error during export: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_qualifying_export()
