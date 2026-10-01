import sys
from pathlib import Path
from core.export_event import export_event_all_sessions
from utils.logging_setup import get_logger
log=get_logger(__name__)
def export_batch(season:int,rounds:list[int],base_dir:str|None=None):
    base_path=Path(base_dir) if base_dir else Path.cwd()/"exports"
    base_path.mkdir(parents=True,exist_ok=True)
    print("="*60)
    print(f"Batch Export - Season {season}")
    print(f"Rounds: {rounds}")
    print(f"Output: {base_path}")
    print("="*60)
    total_success=0
    total_failed=0
    for round_no in rounds:
        print(f"\n{'='*60}")
        print(f"Round {round_no}")
        print("="*60)
        out_dir=base_path/f"{season}_R{round_no:02d}"
        try:
            results=export_event_all_sessions(season,round_no,str(out_dir),verbose=True)
            success=sum(value is not None for value in results.values())
            total_success+=success
            if success:print(f"\nRound {round_no}: {success} sessions exported")
            else:
                print(f"\nRound {round_no}: No data available")
                total_failed+=1
        except Exception as exc:
            log.error("Round %s failed: %s",round_no,exc)
            print(f"\nRound {round_no}: Export failed - {exc}")
            total_failed+=1
    print(f"\n{'='*60}")
    print("Batch Export Summary")
    print("="*60)
    print(f"Total sessions exported: {total_success}")
    print(f"Rounds failed: {total_failed}")
    print(f"Output directory: {base_path}")
    print("="*60)
def main():
    if len(sys.argv)<3:
        print("Usage: python export_batch.py <season> <round_start> [round_end] [output_dir]")
        return 1
    season=int(sys.argv[1])
    start=int(sys.argv[2])
    end=int(sys.argv[3]) if len(sys.argv)>3 else start
    output=sys.argv[4] if len(sys.argv)>4 else None
    export_batch(season,list(range(start,end+1)),output)
    return 0
if __name__=="__main__":
    sys.exit(main())