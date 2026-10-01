import json
import logging
from typing import Callable,Optional
import requests
import sseclient
logger=logging.getLogger(__name__)
class F1DashClient:
    def __init__(self,base_url:str="http://localhost:4000"):
        self.base_url=base_url
        self.sse_url=f"{base_url}/api/sse"
        self.session:Optional[requests.Session]=None
    def connect(self,on_initial:Callable[[dict],None],on_update:Callable[[dict],None],on_error:Callable[[Exception],None]):
        try:
            logger.info(f"Connecting to SSE stream at {self.sse_url}")
            self.session=requests.Session()
            response=self.session.get(self.sse_url,stream=True,timeout=10)
            response.raise_for_status()
            client=sseclient.SSEClient(response)
            for event in client.events():
                try:
                    if event.event=="initial":
                        logger.info("Received initial event")
                        on_initial(json.loads(event.data))
                    elif event.event=="update":
                        on_update(json.loads(event.data))
                    else:
                        logger.debug(f"Unknown event type: {event.event}")
                except json.JSONDecodeError as exc:
                    logger.error(f"Failed to decode JSON: {exc}")
        except requests.exceptions.RequestException as exc:
            logger.error(f"Connection error: {exc}")
            on_error(exc)
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}")
            on_error(exc)
        finally:
            self.disconnect()
    def disconnect(self):
        if self.session:
            self.session.close()
            self.session=None
            logger.info("Disconnected from SSE stream")
    def get_drivers(self)->list:
        try:
            response=requests.get(f"{self.base_url}/api/drivers",timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to get drivers: {exc}")
            return []
    def health_check(self)->bool:
        try:
            response=requests.get(f"{self.base_url}/api/health",timeout=5)
            return response.json().get("success",False)
        except Exception:
            return False