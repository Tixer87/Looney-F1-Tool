# utils/config_loader.py
# Zentrale Konfigurationsloader für das Looney F1 Tool

import json
import os

# Pfad zur config.json (relativ zum Projektroot)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.json')

# Default-Konfiguration als Fallback
DEFAULT_CONFIG = {
    "api_base_url": "http://api.jolpi.ca/ergast/f1",
    "default_year": 2025,
    "default_export_dir": "rlt-ready",
    "live_data_provider": "openf1_connector"
}

_config_cache = None

def load_config():
    """
    Lädt die Konfiguration aus config.json.
    Verwendet Caching, damit die Datei nicht bei jedem Aufruf gelesen wird.
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Merge mit Default-Werten für fehlende Keys
        for key, default_value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_value
        
        _config_cache = config
        return config
        
    except FileNotFoundError:
        print(f"⚠️ Config-Datei nicht gefunden: {CONFIG_PATH}")
        print("📁 Verwende Standard-Konfiguration...")
        _config_cache = DEFAULT_CONFIG.copy()
        return _config_cache
        
    except json.JSONDecodeError as e:
        print(f"❌ Fehler beim Parsen der Config-Datei: {e}")
        print("📁 Verwende Standard-Konfiguration...")
        _config_cache = DEFAULT_CONFIG.copy()
        return _config_cache

def get_config_value(key, default=None):
    """
    Holt einen einzelnen Wert aus der Konfiguration.
    
    Args:
        key (str): Der Schlüssel in der Konfiguration
        default: Fallback-Wert, falls der Schlüssel nicht existiert
    
    Returns:
        Der Konfigurationswert oder der Default-Wert
    """
    config = load_config()
    return config.get(key, default)

def reload_config():
    """
    Forciert das Neuladen der Konfiguration (z.B. nach Änderungen).
    """
    global _config_cache
    _config_cache = None
    return load_config()

# Convenience-Funktionen für häufig verwendete Werte
def get_api_base_url():
    return get_config_value('api_base_url')

def get_default_year():
    return get_config_value('default_year')

def get_default_export_dir():
    return get_config_value('default_export_dir')

def get_live_data_provider():
    return get_config_value('live_data_provider')
