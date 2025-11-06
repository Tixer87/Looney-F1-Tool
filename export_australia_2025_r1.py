"""Export all sessions for Australia 2025 Round 1."""

from core.export_event import export_event_all_sessions

if __name__ == "__main__":
    season = 2025
    round_ = 1
    out_dir = r"C:\Users\ktixe\Documents\LooneyExports\2025_R01_Melbourne"
    
    print("🏎️ Looney F1 Tool - Full Event Export")
    print(f"Event: {season} Round {round_} - Australian Grand Prix")
    
    results = export_event_all_sessions(season, round_, out_dir, verbose=True)
    
    # Show results
    print("\n📊 Final Results:")
    for session, path in results.items():
        status = "✅" if path else "❌"
        print(f"  {status} {session}: {path.name if path else 'Failed'}")
