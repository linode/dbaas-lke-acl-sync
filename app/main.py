'''
 Copyright 2025 Akamai Technologies, Inc.
 
 Licensed under the Apache License, Version 2.0 (the
 "License"); you may not use this file except in
 compliance with the License.  You may obtain a copy
 of the License at

  https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in
writing, software distributed under the License is
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing
permissions and limitations under the License.
'''

from contextlib import asynccontextmanager
import sys
import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from kubernetes_api import KubernetesAPI
from linode_api import LinodeAPI
from accesslist_manager import AccessListManager


# logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

def get_env_var(name, optional=False):
    value = os.getenv(name)
    if not value and optional == False:
        logging.error(f"Missing required environment variable: {name}")
        sys.exit(1)
    return value

# Linode API key
API_KEY = get_env_var("LINODE_API_KEY")

# Postgres database cluster IDS to sync LKE with
DB_PG_CLUSTER_ID_LIST = get_env_var("DATABASE_PG_CLUSTER_IDS", True)

# MySQL database cluster IDS to sync LKE with
DB_MYSQL_CLUSTER_ID_LIST = get_env_var("DATABASE_MYSQL_CLUSTER_IDS", True)

# configmap to hold a list of the last known LKE nodes IPs
NODES_CONFIGMAP_NAME = os.getenv("NODES_CONFIGMAP_NAME", "lke-node-ips")

def get_current_kube_namespace():
    try:
        from kubernetes.config.kube_config import KubeConfigLoader
        import yaml
        kubeconfig_path = os.getenv("KUBECONFIG", os.path.expanduser("~/.kube/config"))
        with open(kubeconfig_path, "r") as f:
            kubeconfig_dict = yaml.safe_load(f)
            loader = KubeConfigLoader(config_dict=kubeconfig_dict)
                        
            # Try to get the namespace from the active context
            namespace = loader.current_context['context']['namespace']
            return namespace
    except Exception as e:
        return None

# configmap namespace for 'NODES_CONFIGMAP_NAME'
NAMESPACE = os.getenv("NAMESPACE") or get_current_kube_namespace()
if not NAMESPACE:
    logging.error("Could not determine Kubernetes namespace. Please set the NAMESPACE environment variable or set Kubectl configuration.")
    sys.exit(1)

# update interval for syncing LKE nodes and DBaaS access list
UPDATE_INTERVAL = os.getenv("UPDATE_INTERVAL", "30")



linode = LinodeAPI(API_KEY)
k8s = KubernetesAPI(NAMESPACE)
manager = AccessListManager(API_KEY, UPDATE_INTERVAL, NODES_CONFIGMAP_NAME,
                            NAMESPACE, DB_PG_CLUSTER_ID_LIST, DB_MYSQL_CLUSTER_ID_LIST)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Access List Sync Service..")

    background_task = asyncio.create_task(manager.sync_loop())

    try:
        yield
    finally:
        logger.info("Shutting down node watcher task...")
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Node watcher task cancelled.")
        

app = FastAPI(lifespan=lifespan, title="LKE + DBaaS ACL Sync")

@app.get("/")
async def index():
    return "LKE DBaaS Access List Sync Service is running."

@app.get("/health")
async def index():
    return {"status": "ok"}

@app.get("/force-next-update")
async def update():
    try:
        result = await manager.clear_cache()

        return {
            "success": "true",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating:{str(e)}")
