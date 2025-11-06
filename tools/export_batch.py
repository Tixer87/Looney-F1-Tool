"""Batch export multiple race weekends."""

import sys
from pathlib import Path
from core.export_event import export_event_all_sessions
from utils.logging_setup import get_logger

log = get_logger(__name__)


def export_batch(season: int, rounds: list[int], base_dir: str = None):
    """
    Export all sessions for multiple rounds.
    
    Args:
        season: Year (e.g., 2025)
        rounds: List of round numbers (e.g., [1, 2, 3])
        base_dir: Base directory for exports (default: C:\Users\ktixe\Documents\LooneyExports)
    """
    if base_dir is None:
        base_dir = r"C:\Users\ktixe\Documents\LooneyExports"
    
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print(f"🏎️ Batch Export - Season {season}")
    print(f"Rounds: {rounds}")
    print(f"Output: {base_path}")
    print("="*60)
    
    total_success = 0
    total_failed = 0
    
    for round_no in rounds:
        print(f"\n{'='*60}")
        print(f"📋 Round {round_no}")
        print(f"{'='*60}")
        
        out_dir = base_path / f"{season}_R{round_no:02d}"
        
        try:
            results = export_event_all_sessions(season, round_no, str(out_dir), verbose=True)
            success_count = sum(1 for v in results.values() if v is not None)
            total_success += success_count
            
            if success_count > 0:
                print(f"\n✅ Round {round_no}: {success_count} sessions exported")
            else:
                print(f"\n⚠️ Round {round_no}: No data available")
                total_failed += 1
                
        except Exception as e:
            log.error(f"Round {round_no} failed: {e}")
            print(f"\n❌ Round {round_no}: Export failed - {e}")
            total_failed += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📊 Batch Export Summary")
    print(f"{'='*60}")
    print(f"✅ Total sessions exported: {total_success}")
    print(f"❌ Rounds failed: {total_failed}")
    print(f"📁 Output directory: {base_path}")
    print(f"{'='*60}\n")


def main():
    """Run batch export from command line."""
    if len(sys.argv) < 3:
        print("Usage: python export_batch.py <season> <round_start> [round_end]")
        print("\nExamples:")
        print("  python export_batch.py 2025 1        # Export round 1 only")
        print("  python export_batch.py 2025 1 5      # Export rounds 1-5")
        print("  python export_batch.py 2025 1 22     # Export full season (rounds 1-22)")
        return 1
    
    season = int(sys.argv[1])
    round_start = int(sys.argv[2])
    round_end = int(sys.argv[3]) if len(sys.argv) > 3 else round_start
    
    rounds = list(range(round_start, round_end + 1))
    export_batch(season, rounds)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
