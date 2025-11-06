"""Event-wide export orchestrator - exports all sessions for a race weekend."""

from pathlib import Path
from typing import Optional
from api.export_service import run_export
from utils.logging_setup import get_logger

log = get_logger(__name__)


def export_event_all_sessions(
    season: int, 
    round_: int, 
    out_dir: str,
    verbose: bool = True
) -> dict[str, Optional[Path]]:
    """
    Export all available sessions for an event.
    Order: FP1, FP2, FP3, Qualifying (Q1/Q2/Q3), Sprint (if available), Race.
    
    Args:
        season: Year (e.g., 2025)
        round_: Round number (1-24)
        out_dir: Output directory for all JSON files
        verbose: Print progress messages
        
    Returns:
        Dictionary mapping session codes to output paths (or None if failed)
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    results = {}
    
    log.info(f"Starting full event export: season={season}, round={round_}")
    if verbose:
        print(f"\n{'='*60}")
        print(f"Exporting ALL Sessions - {season} Round {round_}")
        print(f"Output: {out_dir}")
        print(f"{'='*60}\n")
    
    # Practice Sessions (FP1, FP2, FP3)
    for fp in ("FP1", "FP2", "FP3"):
        try:
            if verbose:
                print(f"\n📋 Exporting {fp}...")
            result = run_export(season, round_, fp, Path(out_dir), verbose=verbose)
            results[fp] = result
        except Exception as e:
            log.warning(f"{fp} skipped: {e}")
            if verbose:
                print(f"⚠️ {fp} skipped: {e}")
            results[fp] = None
    
    # Qualifying (Q exported as Q1/Q2/Q3 split)
    try:
        if verbose:
            print(f"\n📋 Exporting Qualifying (Q1/Q2/Q3)...")
        result = run_export(season, round_, "Q", Path(out_dir), verbose=verbose)
        results["Q"] = result  # Last file (Q3)
    except Exception as e:
        log.warning(f"Qualifying skipped: {e}")
        if verbose:
            print(f"⚠️ Qualifying skipped: {e}")
        results["Q"] = None
    
    # Sprint (optional - only if available)
    # Sprint Qualifying (SQ) would be split into SQ1/SQ2/SQ3 if implemented
    try:
        if verbose:
            print(f"\n📋 Checking for Sprint sessions...")
        # Try Sprint Qualifying
        sq_result = run_export(season, round_, "SQ", Path(out_dir), verbose=verbose)
        results["SQ"] = sq_result
    except Exception as e:
        log.info(f"Sprint Qualifying not available: {e}")
        if verbose:
            print(f"ℹ️ Sprint Qualifying not available")
        results["SQ"] = None
    
    try:
        # Try Sprint Race
        sr_result = run_export(season, round_, "S", Path(out_dir), verbose=verbose)
        results["S"] = sr_result
    except Exception as e:
        log.info(f"Sprint Race not available: {e}")
        if verbose:
            print(f"ℹ️ Sprint Race not available")
        results["S"] = None
    
    # Race (Main Event)
    try:
        if verbose:
            print(f"\n📋 Exporting Race...")
        result = run_export(season, round_, "R", Path(out_dir), verbose=verbose)
        results["R"] = result
    except Exception as e:
        log.error(f"Race export failed: {e}")
        if verbose:
            print(f"❌ Race export failed: {e}")
        results["R"] = None
    
    # Summary
    if verbose:
        print(f"\n{'='*60}")
        print(f"Export Summary:")
        success_count = sum(1 for v in results.values() if v is not None)
        total_count = len(results)
        print(f"✅ Successful: {success_count}/{total_count}")
        print(f"{'='*60}\n")
    
    log.info(f"Event export completed: {success_count}/{total_count} sessions successful")
    return results
