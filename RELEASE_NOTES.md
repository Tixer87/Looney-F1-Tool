# Looney F1 Tool 1.6 – Community Release

## Neu
- GUI-Exporter (tkinter), portable EXE
- Quali/Race/Practice Export
- Sprint optional (fehlende Daten werden sauber behandelt)
- Automatische Ordnererstellung für Export-Ziele
- Session-spezifische Auswahl (Q1/Q2/Q3, Race, Practice)

## Änderungen
- Entkoppelte API-Schicht (`api/export_service.py`)
- Sauberes Ressourcenhandling (mapping/, config.json)
- Vereinfachte Benutzeroberfläche mit Threading
- Entfernung von Web-Interface und Live-Telemetrie-Komponenten
- PyInstaller-kompatible Ressourcenverwaltung

## Bekannte Punkte
- Nicht jede Runde hat Sprint-Daten (kein Fehler, wenn keine Daten)
- Web/UDP nicht enthalten (bewusst entfernt für Community-Release)
- Windows Defender SmartScreen-Warnung möglich (keine Code-Signierung)

## Installation
- Portable Version: ZIP entpacken und `LooneyF1Tool.exe` starten
- Keine Installation erforderlich
- Standard-Export nach `%USERPROFILE%\Documents\RLT` (wird automatisch erstellt)

## Prüfsumme (SHA-256)
```
[HASH_UPDATE_PENDING]
```

**WICHTIG**: Diese Version enthält den korrekten `_internal`-Ordner für PyInstaller 6.x+ und Python 3.13.

## Troubleshooting

### EXE startet nicht
- In neuem Benutzerprofil testen
- Windows Defender Block? → Datei über Eigenschaften → Zulassen
- Antivirus-Ausnahme für LooneyF1Tool.exe hinzufügen

### Kein Export erzeugt
- Runde/Session-Daten kontrollieren
- Bei Sprint kann legitimerweise kein Output entstehen
- Export-Pfad auf Schreibrechte prüfen

### GUI reagiert nicht
- Export läuft im Hintergrund (Progress-Anzeige beachten)
- Bei größeren Dateien kann Export einige Sekunden dauern

## Support
- Issues über GitHub Repository
- Dokumentation in README.md
- MIT License - Open Source Community Tool
