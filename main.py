# main.py
"""
CLI entry point for Looney F1 Tool.
Uses modern export_service with provider router (Jolpica→FastF1 fallback).
"""

import argparse
from pathlib import Path
from api.export_service import run_export
from api.providers.router import get_provider
from utils.logging_setup import get_logger
from core.version import __version__, PRODUCT_NAME

# Initialize logger (will be configured with CLI args)
logger = None

def list_races(year: int):
    """List all races for a season using provider router"""
    try:
        provider = get_provider()
        schedule = provider.schedule(year)
        return schedule
    except Exception as e:
        print(f"❌ Error fetching schedule: {e}")
        return []

def export_session(year: int, round_number: int, session: str, outdir: str | None = None) -> bool:
    """
    Export a session using the modern export_service.
    
    Args:
        year: Season year
        round_number: Race round number
        session: Session type (R, Q, SQ, FP1, etc.)
        outdir: Output directory (default: './out')
    
    Returns:
        True if export succeeded, False otherwise
    """
    if outdir is None:
        outdir = "./out"
    
    out_path = Path(outdir)
    
    try:
        # Type ignore für SessionType - wird zur Laufzeit geprüft
        result = run_export(year, round_number, session, out_path, verbose=True)  # type: ignore
        return result is not None
    except Exception as e:
        print(f"❌ Export failed: {e}")
        logger.error(f"Export failed: {e}", year=year, round=round_number, session=session) if logger else None
        return False

def get_default_year() -> int:
    """Get default year (current year or from config)"""
    from datetime import datetime
    return datetime.now().year

def get_default_export_dir() -> str:
    """Get default export directory"""
    return "./out"

def print_welcome_banner():
    """Schönes ASCII-Banner mit Looney Tunes Branding"""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        console = Console()
        
        console.print(Panel.fit(
            "[bold orange]"
            "     ██╗      ██████╗  ██████╗ ███╗   ██╗███████╗██╗   ██╗    ███████╗  ██╗\n"
            "     ██║     ██╔═══██╗██╔═══██╗████╗  ██║██╔════╝╚██╗ ██╔╝    ██╔════╝ ███║\n"
            "     ██║     ██║   ██║██║   ██║██╔██╗ ██║█████╗   ╚████╔╝     █████╗   ╚██║\n"
            "     ██║     ██║   ██║██║   ██║██║╚██╗██║██╔══╝    ╚██╔╝      ██╔══╝    ██║\n"
            "     ███████╗╚██████╔╝╚██████╔╝██║ ╚████║███████╗   ██║       ██║       ██║\n"
            "     ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝       ╚═╝       ╚═╝\n"
            "[/bold orange]"
            "\n"
            "[bold red]              🏎️ Formula Toons Racing League Tool Export v1.6 🏁[/bold red]\n"
            "[bold red]                     Made with ❤️ for the F1 Community[/bold red]\n\n"
            "[orange]            🏁 Welcome to the ultimate F1 data export tool! 🏁[/orange]\n"
            "[orange]              Transform real F1 data into RLT-ready JSON files[/orange]\n"
            "[yellow]        Perfect for content creators and racing league organizers![/yellow]\n\n"
            "[bold blue]💝 Support Formula Toons on GitHub Sponsors:[/bold blue] [link=https://github.com/sponsors/Tixer87]https://github.com/sponsors/Tixer87[/link]\n",
            border_style="bright_red"
        ))
        
        # Looney Characters Intro
        console.print("\n[bold orange]🐰 Bugs Bunny:[/bold orange] 'Eh, what's up Doc? Ready to export some F1 data?'")
        console.print("[bold red]🐦 Road Runner:[/bold red] 'Meep Meep!' [italic](Translation: Let's go fast!)[/italic]")
        console.print("[bold green]🐸 Kermit:[/bold green] 'It's not easy being green, but exporting data sure is!'")
        
    except ImportError:
        # Fallback ohne Rich
        print("="*70)
        print("🏎️ LOONEY F1 - Formula Toons Export v1.6 🏁")
        print("="*70)
        print("🐰 Welcome to the ultimate F1 data export tool!")
        print("Transform real F1 data into RLT-ready JSON files")
        print("Perfect for content creators and racing league organizers!")
        print()
        print("💝 Support Formula Toons on GitHub Sponsors: https://github.com/sponsors/Tixer87")
        print("="*70)

def main():
    global logger
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Looney F1 Tool - Export F1 data to Racing League Tool format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Support: https://github.com/sponsors/Tixer87"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    parser.add_argument(
        "--demo-log",
        action="store_true",
        help="Enable demo logging to release/v1.7/logs/app_demo.log (for testing)"
    )
    parser.add_argument(
        "--backend",
        choices=["jolpica", "fastf1", "f1dash_live"],
        default="jolpica",
        help="Backend to use: jolpica (default), fastf1, or f1dash_live"
    )
    parser.add_argument(
        "--mode",
        choices=["export", "record"],
        default="export",
        help="Mode: export (default) or record (for live recording)"
    )
    parser.add_argument(
        "--f1dash-url",
        default="http://localhost:4000",
        help="f1-dash URL for live recording (default: http://localhost:4000)"
    )
    parser.add_argument(
        "--output-dir",
        default="./output/live",
        help="Output directory for live recordings (default: ./output/live)"
    )
    
    args = parser.parse_args()
    
    # Handle --version
    if args.version:
        print(__version__)
        raise SystemExit(0)
    
    # Initialize logger with CLI level
    if args.demo_log:
        logger = get_logger("looney", level=args.log_level, logfile="release/v1.7/logs/app_demo.log")
    else:
        logger = get_logger("looney", level=args.log_level)
    
    logger.info(f"Looney F1 Tool {__version__} starting", log_level=args.log_level, backend=args.backend, mode=args.mode)
    
    # Handle live recording mode
    if args.backend == "f1dash_live" and args.mode == "record":
        from live_recorder.recorder import LiveSessionRecorder
        from live_recorder.exporter import LiveToRLTExporter
        from pathlib import Path
        import json
        
        print(f"🎬 Starting f1-dash live recording...")
        print(f"📡 Connecting to: {args.f1dash_url}")
        print(f"💾 Output directory: {args.output_dir}")
        print(f"🛑 Press Ctrl+C to stop recording\n")
        
        recorder = LiveSessionRecorder(f1dash_url=args.f1dash_url)
        
        try:
            recorder.start()
            recorder.wait()  # Blocks until Ctrl+C or session end
        except KeyboardInterrupt:
            print("\n⏹️  Recording stopped by user")
        finally:
            if recorder.state:
                # Export RLT JSON
                recorder.state.freeze()
                exporter = LiveToRLTExporter(recorder.state)
                rlt_json = exporter.export()
                
                # Save to file
                output_path = Path(args.output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                filename = f"{recorder.state.event_name.replace(' ', '_')}_{recorder.state.session_name}_{recorder.state.year}.json"
                filepath = output_path / filename
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(rlt_json, f, indent=2, ensure_ascii=False)
                
                print(f"\n✅ Exported: {filepath}")
                print(f"📊 Drivers: {len(rlt_json['Drivers'])}")
                print(f"🏁 Laps: {recorder.state.current_lap}/{recorder.state.total_laps}")
                print(f"🚨 Safety Cars: {recorder.state.safety_car_count}")
                logger.info("Live recording completed", filepath=str(filepath), drivers=len(rlt_json['Drivers']))
            else:
                print("⚠️  No session data recorded")
                logger.warning("No session data available for export")
        
        return
    
    print_welcome_banner()
    print()
    print("If you hear a 'Meep Meep', don't worry – that's just Roadrunner overtaking your data speed! 🏎️💨\n")

    while True:
        # Select year
        default_year = get_default_year()
        year_input = input(f"📅 Enter season year (default: {default_year}): ").strip()
        if not year_input:
            year = default_year
        elif not year_input.isdigit():
            print("🦆 Daffy says: 'You're despicable!' Please enter a valid year!")
            continue
        else:
            year = int(year_input)

        # List races
        logger.debug("Fetching race list", year=year)
        races = list_races(year)
        if not races:
            logger.warning("No races found", year=year)
            print(f"😱 No races found for {year}. Try another year. Maybe Wile E. Coyote stole the calendar?")
            continue

        logger.info("Races loaded", year=year, count=len(races))
        print(f"\n🏟️ Available races in {year}:")
        for idx, race in enumerate(races, 1):
            # Provider liefert circuitFullName direkt
            circuit = race.get('circuitFullName', race.get('Circuit', {}).get('circuitName', 'Unknown'))
            race_name = race.get('raceName', f'Round {race.get("round", idx)}')
            date = race.get('date', 'TBD')
            print(f"{idx}. {race_name} ({circuit}, {date})")

        # Select race
        while True:
            choice = input("🎯 Select a race by number: ").strip()
            if not choice.isdigit() or not (1 <= int(choice) <= len(races)):
                print("🔫 Elmer Fudd whispers: 'Be vewy vewy careful... pick a valid number!'")
                continue
            round_number = int(races[int(choice)-1]["round"])
            selected_race = races[int(choice)-1]
            circuit = selected_race.get('circuitFullName', selected_race.get('Circuit', {}).get('circuitName', 'Unknown'))
            race_name = selected_race.get('raceName', f'Round {round_number}')
            date = selected_race.get('date', 'TBD')
            print(f"\n🦆 Daffy Duck shouts: 'You picked {race_name} at {circuit} on {date}! That's a quacker of a choice!'")
            break

        # Export sessions
        print("\n🗂️ Which sessions do you want to export?")
        print("1️⃣  Qualifying (Q1/Q2/Q3) – 'What's up, doc? Let's see who's fastest!' 🥕")
        print("2️⃣  Sprint – 'Speedy Gonzales would love this one!' 🐭")
        print("3️⃣  Race – 'The main event! Even Wile E. Coyote can't catch up!' 🐺")
        print("4️⃣  All – 'Go all-in, like Taz at a buffet!' 🌪️")
        print("💡 Bugs Bunny tip: You can choose multiple, like '1 3' for Qualifying and Race!")
        session_choice = input("👉 Enter your choice (e.g. 1 3): ").strip().split()
        session_map = {"1": "qualifying", "2": "sprint", "3": "results"}
        sessions = []
        if "4" in session_choice:
            sessions = ["qualifying", "sprint", "results"]
        else:
            for s in session_choice:
                if s in session_map:
                    sessions.append(session_map[s])
        if not sessions:
            print("🐷 Porky Pig stutters: 'Th-th-th-that's not a valid choice, folks!' Try again.")
            continue

        print("\n💾 Where should the exported files be saved?")
        default_dir = get_default_export_dir()
        print(f"Just press Enter to use the default folder: {default_dir}")
        print("🐦 Tweety says: 'I tawt I taw a directory!'")
        outdir = input(f"📁 Export directory [{default_dir}]: ").strip()
        if not outdir:
            outdir = default_dir

        for session in sessions:
            if session == "qualifying":
                # Modern export nutzt Q1, Q2, Q3 direkt
                quali_messages = {
                    "Q1": "🐦 Road Runner says: 'Meep Meep! Let's get started with Q1!'",
                    "Q2": "🦊 Wile E. Coyote grumbles: 'Time for Q2... this time I'll catch 'em!'",
                    "Q3": "🐰 Bugs Bunny winks: 'Eh, Q3? Only the fastest survive, doc!'"
                }
                for quali_phase in ["Q1", "Q2", "Q3"]:
                    print(f"🚦 Exporting {quali_phase}... {quali_messages[quali_phase]}")
                    success = export_session(year, round_number, quali_phase, outdir=outdir)
                    if success:
                        print(f"✅ Export completed!")
            elif session == "sprint":
                print("🏁 Exporting Sprint... 🐰 Lola Bunny cheers: 'Let's hop to it, racers!'")
                success = export_session(year, round_number, "SQ", outdir=outdir)
                if success:
                    print(f"✅ Export completed!")
            elif session == "results":
                print("🏁 Exporting Race... 🐸 Kermit waves: 'It's not easy being green, but exporting is a breeze!'")
                success = export_session(year, round_number, "R", outdir=outdir)
                if success:
                    print(f"✅ Export completed!")
            else:
                print("🎩 Roger Rabbit shouts: 'P-p-please export this session, Eddie!'")
                success = export_session(year, round_number, session, outdir=outdir)
                if success:
                    print(f"✅ Export completed!")

        again = input("\n🔁 Do you want to export another race? (y/n): ").strip().lower()
        if again != "y":
            print_goodbye_banner()
            break

def print_goodbye_banner():
    """Schöne Verabschiedung mit Looney Tunes Branding"""
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        
        goodbye_text = """
        [bold orange]🏁 Export Complete! 🏁[/bold orange]

        [green]✅ Your F1 data has been successfully converted to RLT format![/green]
        [yellow]📁 Files are ready to use in Racing League Tool[/yellow]

        [bold blue]🐰 Bugs Bunny:[/bold blue] "Ain't I a stinker? Thanks for using our tool, Doc!"
        [bold red]🐦 Road Runner:[/bold red] "Meep Meep!" [italic](See you at the next race!)[/italic]
        [bold magenta]🦆 Daffy Duck:[/bold magenta] "You're despicably good at exporting data!"

        [bold yellow]🙏 Special Thanks:[/bold yellow]
        [bold orange]• F1 SRL Sim Racing League:[/bold orange] 
        [bold orange]• Racing League Tool (RLT):[/bold orange] https://github.com/Tixer87/Racing-League-Tools-Public
        [bold orange]• Jolpica F1 API:[/bold orange] https://github.com/jolpica/jolpica-f1

        [bold blue]💝 Support Formula Toons on GitHub Sponsors:[/bold blue] https://github.com/sponsors/Tixer87
        """
        
        console.print(Panel.fit(
            goodbye_text,
            title="[bold red]🎬 That's All Folks! 🎬[/bold red]",
            border_style="bright_green"
        ))
        
    except ImportError:
        print("="*60)
        print("🏁 Export Complete! Thanks for using Looney F1 Tool! 🏁")
        print("🐰 Bugs Bunny: 'Ain't I a stinker? See you next time, Doc!'")
        print("🐦 Road Runner: 'Meep Meep!' (See you at the next race!)")
        print("💝 Support Formula Toons on GitHub Sponsors: https://github.com/sponsors/Tixer87")
        print("🎬 That's all folks! 🎬")
        print("="*60)

def export_from_gui(season: int, round_no: int, session: str, out_dir: str, verbose: bool=False) -> str:
    """
    Programmatischer Einstieg für GUI/EXE mit Session-Gruppen-Support.
    """
    from pathlib import Path
    from api.export_service import run_export, SessionType, expand_session_group
    from typing import cast
    
    # Expand session group to individual sessions
    session_codes = expand_session_group(session)
    
    if len(session_codes) > 1:
        # Export multiple sessions (group or "All Sessions")
        print(f"Exporting {len(session_codes)} sessions for Season {season}, Round {round_no}: {session_codes}")
        results = []
        
        for code in session_codes:
            try:
                # Validate session code
                valid_session_codes = {"FP1", "FP2", "FP3", "Q1", "Q2", "Q3", "P", "Q", "SQ", "SS", "S", "R"}
                if code in valid_session_codes:
                    session_typed = cast(SessionType, code)
                    result = run_export(season=season, round_no=round_no, session=session_typed, out_dir=Path(out_dir), verbose=verbose)
                    if result:
                        results.append(str(result))
                        print(f"✅ Exported {code}: {result}")
            except Exception as e:
                print(f"⚠️ Session {code} failed: {e}")
        
        return f"Exported {len(results)} sessions to {out_dir}"
    
    # Single session export
    single_session = session_codes[0]
    valid_session_codes = {"FP1", "FP2", "FP3", "Q1", "Q2", "Q3", "P", "Q", "SQ", "SS", "S", "R"}
    
    if single_session not in valid_session_codes:
        raise ValueError(f"Invalid session type: {single_session}. Must be one of {valid_session_codes}")
    
    session_typed = cast(SessionType, single_session)
    result = run_export(season=season, round_no=round_no, session=session_typed, out_dir=Path(out_dir), verbose=verbose)
    return str(result)

if __name__ == "__main__":
    main()

def fetch_race_data(year, round_number=None, endpoint="results"):
    # Use the existing API function
    from api.jolpica_api import fetch_race_data as api_fetch_race_data
    return api_fetch_race_data(year, round_number, endpoint)
