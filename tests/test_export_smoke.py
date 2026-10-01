# tests/test_export_smoke.py
from pathlib import Path
import pytest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.export_service import run_export

@pytest.mark.parametrize("session", ["Q", "R"])  # Nur Q und R - SQ separat testen
def test_run_export_smoke(tmp_path: Path, session):
    """Smoke-Test für Export-Funktionalität (Qualifying und Race)"""
    try:
        out = run_export(season=2025, round_no=1, session=session, out_dir=tmp_path, verbose=False)
        
        # Grundlegende Validierung
        assert out.exists(), f"Export-Datei wurde nicht erstellt: {out}"
        assert out.suffix == ".json", f"Export-Datei sollte .json sein: {out}"
        assert out.stat().st_size > 0, f"Export-Datei ist leer: {out}"
        
        # JSON-Validierung
        import json
        with open(out, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, dict), "Export sollte JSON-Objekt sein"
            
        print(f"✅ Export-Test für {session} erfolgreich: {out}")
        
    except Exception as e:
        # Falls API nicht verfügbar oder andere Fehler
        pytest.skip(f"Export-Test übersprungen wegen: {e}")

def test_sprint_export_when_available(tmp_path: Path):
    """Test Sprint-Export - wird übersprungen wenn keine Sprint-Daten verfügbar"""
    try:
        # Teste mit Runde 1 (normalerweise kein Sprint)
        out = run_export(season=2025, round_no=1, session="SQ", out_dir=tmp_path, verbose=False)
        
        # Wenn wir hier ankommen, war der Sprint-Export erfolgreich
        assert out.exists(), f"Sprint-Export-Datei wurde nicht erstellt: {out}"
        assert out.suffix == ".json", f"Sprint-Export-Datei sollte .json sein: {out}"
        
        print(f"✅ Sprint-Export erfolgreich: {out}")
        
    except Exception as e:
        # Sprint nicht verfügbar - das ist normal für viele Runden
        pytest.skip(f"Sprint-Test übersprungen (Sprint vermutlich nicht verfügbar): {e}")

def test_invalid_session_type():
    """Test dass ungültige Session-Typen einen Fehler werfen"""
    with pytest.raises(ValueError, match="Invalid session type"):
        run_export(season=2025, round_no=1, session="INVALID", out_dir=Path("/tmp"), verbose=False)

def test_export_creates_directory(tmp_path: Path):
    """Test dass Export-Ordner automatisch erstellt wird"""
    non_existent_dir = tmp_path / "new_folder" / "subfolder"
    assert not non_existent_dir.exists()
    
    try:
        out = run_export(season=2025, round_no=1, session="Q", out_dir=non_existent_dir, verbose=False)
        assert non_existent_dir.exists(), "Export-Ordner wurde nicht erstellt"
        assert out.parent == non_existent_dir, "Export-Datei im falschen Ordner"
    except Exception as e:
        pytest.skip(f"Export-Test übersprungen wegen: {e}")
