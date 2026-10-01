from typing import Any,Dict,List,Literal,Optional,Protocol
SessionType=Literal["P","Q","SQ","R"]
class ProviderError(Exception):pass
class ProviderUnavailable(ProviderError):pass
class ProviderTimeout(ProviderError):pass
class ProviderDataError(ProviderError):pass
class DataProvider(Protocol):
    def schedule(self,season:int)->List[Dict[str,Any]]:...
    def export_payload(self,season:int,round_no:int,session:SessionType)->Optional[Dict[str,Any]]:...