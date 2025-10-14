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

import ipaddress
import logging
import sys
from kubernetes import client as k8s_client, config as k8s_config
from datetime import datetime


logger = logging.getLogger(__name__)

DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"


class KubernetesAPI:
    def __init__(self, namespace):
        try:
            k8s_config.load_incluster_config()  # use in-cluster config
            sa = self.v1.read_namespaced_service_account('default', self.namespace)

        except Exception:
            try:
                k8s_config.load_kube_config()  # fallback for local development
            except Exception as e:
                print(f"Failed to load Kubernetes configuration: {e}")
                sys.exit(1)
        self.v1 = k8s_client.CoreV1Api()
        self.namespace = namespace

    def get_node_ip_list(self):
        """Fetch list of Internal IPs of all Nodes in the Kubernetes cluster."""
        nodes = self.v1.list_node().items

        ips = []
        for node in nodes:
            addresses = node.status.addresses
            for addr in addresses:
                if addr.type == "ExternalIP":
                    if isinstance(ipaddress.ip_address(addr.address), ipaddress.IPv4Address):
                        ips.append(addr.address+"/32")
        return sorted(ips)

    def load_old_ips_from_configmap(self, configmap_name):
        """Load old IPs from a ConfigMap."""
        logger.info(
            f"Getting Old IPs from : {configmap_name} in namespace: {self.namespace}")
        try:
            configmap = self.v1.read_namespaced_config_map(
                configmap_name, self.namespace)
            
            ips_string = configmap.data.get("last_node_ips", "")
            last_update_str = configmap.data.get("last_update", "")
            last_update = None
            
            if len(last_update_str) > 0:
                last_update = datetime.strptime(last_update_str, DATE_FORMAT_STR)
            if ips_string:
                return sorted(ips_string.split(',')), last_update
            return []
        except k8s_client.exceptions.ApiException as e:
            if e.status == 404:
                return [], None
            else:
                print(f"Error reading ConfigMap: {e}")
                sys.exit(1)

    def create_or_update_configmap(self, configmap_name, ips):
        """Create or update a ConfigMap with given IPs."""
        csv_ips = ",".join(ips)

        configmap_contents = k8s_client.V1ConfigMap(
            metadata=k8s_client.V1ObjectMeta(
                name=configmap_name, namespace=self.namespace),
            data={"last_node_ips": csv_ips, "last_update": datetime.now().strftime(DATE_FORMAT_STR)}
        )

        try:
            resp = self.v1.replace_namespaced_config_map(
                configmap_name, self.namespace, configmap_contents)
        except k8s_client.exceptions.ApiException as e:
            if e.status == 404:
                resp = self.v1.create_namespaced_config_map(
                    self.namespace, configmap_contents)
            else:
                logging.error(f"Error updating ConfigMap: {e}")
                sys.exit(1)

    def try_delete_configmap(self, configmap_name):
        try:
            self.v1.read_namespaced_config_map(configmap_name, self.namespace)
            self.v1.delete_namespaced_config_map(configmap_name, self.namespace)
        except Exception as e:
            if "not found" in str(e):
                return True
            else:
                return False
