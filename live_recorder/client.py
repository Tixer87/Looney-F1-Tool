"""
SSE Client für f1-dash Live Service
"""

import json
import logging
from typing import Callable, Optional
import requests
import sseclient

logger = logging.getLogger(__name__)


class F1DashClient:
    """SSE Client für f1-dash Live Service"""
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url
        self.sse_url = f"{base_url}/api/sse"
        self.session: Optional[requests.Session] = None
    
    def connect(
        self,
        on_initial: Callable[[dict], None],
        on_update: Callable[[dict], None],
        on_error: Callable[[Exception], None]
    ):
        """
        Verbinde zu SSE Stream und verarbeite Events
        
        Args:
            on_initial: Callback für initial-Event
            on_update: Callback für update-Events
            on_error: Callback bei Fehlern
        """
        try:
            logger.info(f"Connecting to SSE stream at {self.sse_url}")
            
            self.session = requests.Session()
            response = self.session.get(self.sse_url, stream=True, timeout=10)
            response.raise_for_status()
            
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                try:
                    if event.event == "initial":
                        logger.info("Received initial event")
                        data = json.loads(event.data)
                        on_initial(data)
                    
                    elif event.event == "update":
                        data = json.loads(event.data)
                        on_update(data)
                    
                    else:
                        logger.debug(f"Unknown event type: {event.event}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON: {e}")
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {e}")
            on_error(e)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            on_error(e)
        
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Verbindung trennen"""
        if self.session:
            self.session.close()
            self.session = None
            logger.info("Disconnected from SSE stream")
    
    def get_drivers(self) -> list:
        """
        Abrufen der Fahrerliste via REST
        
        Returns:
            list: Liste der Fahrer-Dicts
        """
        try:
            response = requests.get(f"{self.base_url}/api/drivers", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get drivers: {e}")
            return []
    
    def health_check(self) -> bool:
        """
        Health Check
        
        Returns:
            bool: True wenn f1-dash erreichbar und healthy
        """
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            data = response.json()
            return data.get("success", False)
        except:
            return False
