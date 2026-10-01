from pathlib import Path
from typing import Optional
from api.export_service import run_export
from utils.logging_setup import get_logger
log=get_logger(__name__)
def export_event_all_sessions(season:int,round_:int,out_dir:str,verbose:bool=True)->dict[str,Optional[Path]]:
    out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    results={}
    log.info("Starting full event export: season=%s, round=%s",season,round_)
    if verbose:
        print(f"\n{'='*60}")
        print(f"Exporting ALL Sessions - {season} Round {round_}")
        print(f"Output: {out_dir}")
        print(f"{'='*60}\n")
    for session in ("FP1","FP2","FP3"):
        try:
            if verbose:print(f"\nExporting {session}...")
            results[session]=run_export(season,round_,session,out,verbose=verbose)
        except Exception as exc:
            log.warning("%s skipped: %s",session,exc)
            if verbose:print(f"{session} skipped: {exc}")
            results[session]=None
    try:
        if verbose:print("\nExporting Qualifying (Q1/Q2/Q3)...")
        results["Q"]=run_export(season,round_,"Q",out,verbose=verbose)
    except Exception as exc:
        log.warning("Qualifying skipped: %s",exc)
        if verbose:print(f"Qualifying skipped: {exc}")
        results["Q"]=None
    try:
        if verbose:print("\nChecking for Sprint sessions...")
        results["SQ"]=run_export(season,round_,"SQ",out,verbose=verbose)
    except Exception as exc:
        log.info("Sprint Qualifying not available: %s",exc)
        if verbose:print("Sprint Qualifying not available")
        results["SQ"]=None
    try:
        results["S"]=run_export(season,round_,"S",out,verbose=verbose)
    except Exception as exc:
        log.info("Sprint Race not available: %s",exc)
        if verbose:print("Sprint Race not available")
        results["S"]=None
    try:
        if verbose:print("\nExporting Race...")
        results["R"]=run_export(season,round_,"R",out,verbose=verbose)
    except Exception as exc:
        log.error("Race export failed: %s",exc)
        if verbose:print(f"Race export failed: {exc}")
        results["R"]=None
    success_count=sum(value is not None for value in results.values())
    total_count=len(results)
    if verbose:
        print(f"\n{'='*60}")
        print("Export Summary:")
        print(f"Successful: {success_count}/{total_count}")
        print(f"{'='*60}\n")
    log.info("Event export completed: %s/%s sessions successful",success_count,total_count)
    return results