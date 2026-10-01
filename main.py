import argparse
from datetime import datetime
from pathlib import Path
from typing import cast
from api.export_service import SessionType,expand_session_group,run_export
from api.providers.router import get_provider
from core.version import PRODUCT_NAME,__version__
from utils.config_loader import get_default_export_dir
from utils.logging_setup import get_context_logger
logger=None
VALID_SESSIONS={"FP1","FP2","FP3","P","Q","Q1","Q2","Q3","SQ","SS","S","R"}
def list_races(year:int):
    try:return get_provider(year=year).schedule(year)
    except Exception as exc:
        print(f"Error fetching schedule: {exc}")
        return []
def export_session(year:int,round_number:int,session:str,outdir:str|None=None)->bool:
    global logger
    try:
        result=run_export(year,round_number,cast(SessionType,session),Path(outdir or get_default_export_dir()),verbose=True)
        return result is not None
    except Exception as exc:
        print(f"Export failed: {exc}")
        if logger:logger.error("Export failed",year=year,round=round_number,session=session,error=exc)
        return False
def export_from_gui(season:int,round_no:int,session:str,out_dir:str,verbose:bool=False)->str:
    codes=expand_session_group(session)
    results=[]
    for code in codes:
        if code not in VALID_SESSIONS:raise ValueError(f"Invalid session type: {code}")
        try:
            result=run_export(season,round_no,cast(SessionType,code),Path(out_dir),verbose=verbose)
            if result:results.append(str(result))
        except Exception as exc:
            if verbose:print(f"Session {code} failed: {exc}")
    if len(codes)>1:return f"Exported {len(results)} sessions to {out_dir}"
    return results[0] if results else ""
def fetch_race_data(year,round_number=None,endpoint="results"):
    from api.jolpica_api import fetch_race_data as fetch
    return fetch(year,round_number,endpoint)
def _event_text(event,index):
    round_no=event.get("round",index)
    name=event.get("raceName",f"Round {round_no}")
    circuit=event.get("circuitFullName") or event.get("Circuit",{}).get("circuitName") or event.get("Location","Unknown")
    date=event.get("date","TBD")
    return round_no,name,circuit,date
def interactive():
    while True:
        default_year=datetime.now().year
        raw=input(f"Season [{default_year}]: ").strip()
        if raw and not raw.isdigit():
            print("Invalid season.")
            continue
        year=int(raw) if raw else default_year
        races=list_races(year)
        if not races:
            print(f"No races found for {year}.")
            continue
        print(f"\nF1 {year}")
        for index,event in enumerate(races,1):
            _,name,circuit,date=_event_text(event,index)
            print(f"{index}. {name} | {circuit} | {date}")
        while True:
            raw=input("\nRace number: ").strip()
            if raw.isdigit() and 1<=int(raw)<=len(races):break
            print("Invalid selection.")
        event=races[int(raw)-1]
        round_no=int(event["round"])
        print("\n1. Practice")
        print("2. Qualifying")
        print("3. Sprint")
        print("4. Race")
        print("5. All Sessions")
        groups={"1":"Practice","2":"Qualifying","3":"Sprint","4":"Race","5":"All Sessions"}
        choice=input("Session: ").strip()
        if choice not in groups:
            print("Invalid selection.")
            continue
        out_dir=input(f"Output folder [{get_default_export_dir()}]: ").strip() or get_default_export_dir()
        print(export_from_gui(year,round_no,groups[choice],out_dir,True))
        if input("\nExport another race? [y/N]: ").strip().lower()!="y":break
def main():
    global logger
    parser=argparse.ArgumentParser(description=f"{PRODUCT_NAME} {__version__}")
    parser.add_argument("--version",action="store_true")
    parser.add_argument("--log-level",choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"],default="INFO")
    parser.add_argument("--year",type=int)
    parser.add_argument("--round",type=int,dest="round_no")
    parser.add_argument("--session",choices=sorted(VALID_SESSIONS|{"ALL"}))
    parser.add_argument("--output-dir",default=get_default_export_dir())
    args=parser.parse_args()
    if args.version:
        print(__version__)
        return
    logger=get_context_logger("looney",level=args.log_level)
    logger.info(f"{PRODUCT_NAME} {__version__} starting")
    supplied=(args.year is not None,args.round_no is not None,args.session is not None)
    if any(supplied):
        if not all(supplied):parser.error("--year, --round and --session must be supplied together")
        codes=["FP1","FP2","FP3","Q","SQ","S","R"] if args.session=="ALL" else [args.session]
        results=[]
        for code in codes:
            result=run_export(args.year,args.round_no,cast(SessionType,code),Path(args.output_dir),verbose=True)
            if result:results.append(result)
        raise SystemExit(0 if results else 1)
    interactive()
if __name__=="__main__":
    main()