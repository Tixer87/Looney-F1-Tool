from .jolpica_provider import JolpicaProvider
from . import fastf1_provider as ff1
class FastF1ProviderWrapper:
    name="fastf1"
    def is_available(self)->bool:
        return True
    def schedule(self,year:int)->list[dict]:
        return ff1.schedule(year)
    def fetch_session_raw(self,year:int,round_no:int,session_type:str)->dict:
        payload=ff1.export_payload(year,round_no,session_type)
        if payload:return payload
        return {"provider":self.name,"year":year,"round":round_no,"sessionType":session_type,"Drivers":[]}
def get_provider(prefer:str|None=None,year:int|None=None):
    if prefer=="fastf1":return FastF1ProviderWrapper()
    if prefer=="jolpica":
        provider=JolpicaProvider()
        return provider if provider.is_available() else FastF1ProviderWrapper()
    if year and year>=2023:return FastF1ProviderWrapper()
    provider=JolpicaProvider()
    return provider if provider.is_available() else FastF1ProviderWrapper()