import json
from utils.logging_setup import get_logger

# Initialize logger
log = get_logger(__name__)

DRIVERS_FILE = "mapping/drivers.json"

def get_local_drivers():
    """Lädt die Fahrerdaten aus der lokalen JSON-Datei."""
    with open(DRIVERS_FILE, 'r') as f:
        return json.load(f)

def find_driver_by_jolpica_id(jolpica_id, local_drivers):
    """Sucht einen Fahrer in der lokalen Liste anhand der jolpicaId."""
    for driver in local_drivers:
        if driver.get('jolpicaId') == jolpica_id:
            return driver
    return None

def map_driver_to_rlt(jolpica_driver, local_drivers):
    """
    Wandelt Jolpica-Fahrer in das RLT-kompatible Format um,
    indem die lokalen Daten als "Source of Truth" verwendet werden.
    """
    jolpica_id = jolpica_driver.get('driverId')
    local_driver = find_driver_by_jolpica_id(jolpica_id, local_drivers)

    if local_driver:
        # Lokale Daten bevorzugen
        return {
            "Name": local_driver['Name'],
            "Nationality": local_driver['Nationality'],
            "RaceNumber": local_driver.get('RaceNumber', '0'),
            "DriverId": jolpica_id
        }
    else:
        # Fallback auf Jolpica-Daten, falls der Fahrer lokal nicht gefunden wird
        return {
            "Name": f"{jolpica_driver['givenName']} {jolpica_driver['familyName']}",
            "Nationality": jolpica_driver['nationality'],
            "RaceNumber": jolpica_driver.get('permanentNumber', '0'),
            "DriverId": jolpica_id
        }

def map_all_drivers(jolpica_drivers):
    """Wandelt eine Liste von Jolpica-Fahrern in das RLT-Format um."""
    local_drivers = get_local_drivers()
    return [map_driver_to_rlt(driver, local_drivers) for driver in jolpica_drivers]

def sync_drivers_with_jolpica(jolpica_drivers):
    """
    Vergleicht die lokale Fahrerliste mit den Daten von Jolpica und
    identifiziert neue oder zu aktualisierende Fahrer.
    """
    local_drivers = get_local_drivers()
    local_driver_map = {d['jolpicaId']: d for d in local_drivers if 'jolpicaId' in d}

    new_drivers = []
    updated_drivers = []

    for jolpica_driver in jolpica_drivers:
        jolpica_id = jolpica_driver['driverId']
        if jolpica_id not in local_driver_map:
            new_drivers.append(jolpica_driver)
        else:
            # Optional: Detailliertere Vergleiche für Aktualisierungen hinzufügen
            pass

    # Hier könnten Sie die neuen/aktualisierten Fahrer in eine Datei schreiben
    # oder in der Konsole ausgeben.
    if new_drivers:
        log.info("New drivers found", count=len(new_drivers))
        for driver in new_drivers:
            log.debug("New driver", 
                     name=f"{driver['givenName']} {driver['familyName']}", 
                     id=driver['driverId'])

    return new_drivers, updated_drivers