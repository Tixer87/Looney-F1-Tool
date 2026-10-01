import json
import os
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
CONFIG_PATH=os.path.join(PROJECT_ROOT,"config.json")
DEFAULT_CONFIG={
    "api_base_url":"http://api.jolpi.ca/ergast/f1",
    "default_year":2025,
    "default_export_dir":"rlt-ready",
    "live_data_provider":"openf1_connector"
}
_config_cache=None
def load_config():
    global _config_cache
    if _config_cache is not None:return _config_cache
    try:
        with open(CONFIG_PATH,"r",encoding="utf-8") as f:config=json.load(f)
        for key,value in DEFAULT_CONFIG.items():config.setdefault(key,value)
        _config_cache=config
    except FileNotFoundError:
        print(f"Config file not found: {CONFIG_PATH}")
        _config_cache=DEFAULT_CONFIG.copy()
    except json.JSONDecodeError as exc:
        print(f"Invalid config file: {exc}")
        _config_cache=DEFAULT_CONFIG.copy()
    return _config_cache
def get_config_value(key,default=None):
    return load_config().get(key,default)
def reload_config():
    global _config_cache
    _config_cache=None
    return load_config()
def get_api_base_url():
    return get_config_value("api_base_url")
def get_default_year():
    return get_config_value("default_year")
def get_default_export_dir():
    return get_config_value("default_export_dir")
def get_live_data_provider():
    return get_config_value("live_data_provider")