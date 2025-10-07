import logging
import os
import requests

API_URL = os.getenv("LINODE_API_URL", "https://api.linode.com/v4")  # Default fallback if not set

logger = logging.getLogger(__name__)

class LinodeAPI:
    def __init__(self, api_key):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }        

    def _get(self, endpoint):
        resp = requests.get(f"{API_URL}{endpoint}", headers=self.headers)
        logging.debug(resp.text)
        if not resp.ok:
            logging.error(f"GET {endpoint} failed: {resp.status_code} {resp.text}")
        return resp.json()

    def _put(self, endpoint, payload):
        resp = requests.put(f"{API_URL}{endpoint}", headers=self.headers, json=payload)
        logging.debug(resp.text)
        if not resp.ok:
            logging.error(f"PUT {endpoint} failed: {resp.status_code} {resp.text}")
        return resp.json()
    
    def get_db_allow_list(self, db_type, db_cluster_id):
        db = self._get(f"/databases/{db_type}/instances/{db_cluster_id}")
        return db.get("allow_list", [])

    def update_db_allow_list(self, db_type, db_cluster_id, ips):
        payload = {"allow_list": ips}
        self._put(f"/databases/{db_type}/instances/{db_cluster_id}", payload)