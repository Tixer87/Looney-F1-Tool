from utils.logging_setup import get_logger
log=get_logger(__name__)
def map_driver_to_rlt(driver):
    return {"Name":" ".join(x for x in (driver.get("givenName",""),driver.get("familyName","")) if x).strip(),"Nationality":driver.get("nationality","Unknown"),"RaceNumber":driver.get("permanentNumber","0"),"DriverId":driver.get("driverId","")}
def map_all_drivers(drivers):
    return [map_driver_to_rlt(driver) for driver in drivers]
def sync_drivers_with_jolpica(drivers):
    log.info("Driver sync uses Jolpica as source of truth",count=len(drivers))
    return drivers,[]