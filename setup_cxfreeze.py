# setup_cxfreeze.py
from cx_Freeze import setup, Executable
import sys

# Optimierte Includes - nur was wirklich gebraucht wird
build_exe_options = {
    "includes": [
        "api.export_service",
        "api.providers.router",
        "api.providers.jolpica_provider",
        "api.providers.jolpica_api",
        "api.providers.fastf1_provider",
        "api.providers.base",
        "api.providers.aggregate",
        "api.data_mapper",
        "api.jolpica_api",
        "export.rlt_adapter",
        "export.rlt_enums",
        "mapping.drivers_aliases",
        "mapping.teams_aliases",
        "mapping.drivers_nations",
        "mapping.circuit_aliases",
        "mapping.normalize",
        "fastf1.events",
        "fastf1.api",
        "fastf1.core",
        "pandas",
        "numpy",
        "utils.logging_setup",
        "utils.config_loader",
        "core.version",
    ],
    "packages": ["api", "export", "mapping", "utils", "core"],
    "include_files": [
        ("mapping/circuits.json", "mapping/circuits.json"),
        ("mapping/teams.f1.json", "mapping/teams.f1.json"),
        ("mapping/lineups.f1.json", "mapping/lineups.f1.json"),
        ("mapping/championships.json", "mapping/championships.json"),
        ("mapping/drivers.json", "mapping/drivers.json"),
        ("mapping/nations.json", "mapping/nations.json"),
        ("mapping/driver_alias_map.json", "mapping/driver_alias_map.json"),
        ("mapping/nations_alias_map.json", "mapping/nations_alias_map.json"),
        ("mapping/team_alias_map.json", "mapping/team_alias_map.json"),
        ("mapping/cars.f1.json", "mapping/cars.f1.json"),
        ("config.json", "config.json"),
        ("VERSION", "VERSION"),
    ],
    "excludes": [
        "tests", 
        "tkinter", 
        "matplotlib",           # NICHT benötigt
        "matplotlib.tests", 
        "numpy.tests", 
        "pandas.tests",
        "PyQt5",                # Falls vorhanden, aber nicht genutzt
        "PyQt6",                # Falls vorhanden, aber nicht genutzt
        "PySide6",              # Falls vorhanden, aber nicht genutzt
    ],
    "include_msvcr": True,
    "optimize": 1,
    "silent": False,            # Zeigt Fortschritt
}

executables = [
    Executable(
        "gui_app.py",
        base="Win32GUI",            # GUI ohne Konsole
        target_name="LooneyF1Tool.exe",
        icon="icon.ico",            # Looney F1 Tool Logo
    )
]

# Version aus core.version importieren
try:
    from core.version import __version__ as VERSION
except Exception:
    VERSION = "1.7.2_beta"

setup(
    name="Looney F1 Tool",
    version=VERSION,
    description="Looney F1 Tool – F1 session exports with Jolpica/FastF1",
    options={"build_exe": build_exe_options},
    executables=executables,
)
