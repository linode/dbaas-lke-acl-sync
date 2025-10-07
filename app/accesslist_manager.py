
import asyncio
from datetime import datetime
import logging
import numpy as np

from kubernetes_api import KubernetesAPI
from linode_api import LinodeAPI

DATABASE_TYPE_PG = "postgresql"
DATABASE_TYPE_MYSQL = "mysql"


class AccessListManager:
    def __init__(self, linode_api_key, update_interval, configmap_name, namespace, database_pg_cluster_id_list, database_mysql_cluster_id_list):
        self.k8s = KubernetesAPI(namespace)
        self.logger = logging.getLogger(__name__)
        self.linode = LinodeAPI(linode_api_key)
        self.update_interval = update_interval
        self.configmap_name = configmap_name
        self.database_pg_cluster_id_list = database_pg_cluster_id_list
        self.database_mysql_cluster_id_list = database_mysql_cluster_id_list
        self.logger.info(database_pg_cluster_id_list)
        self.logger.info(database_mysql_cluster_id_list)

    async def sync_loop(self):
        try:
            while True:
                current_ips = await asyncio.to_thread(self.k8s.get_node_ip_list)
                cache_data = await asyncio.to_thread(self.k8s.load_old_ips_from_configmap, self.configmap_name)
                old_ips = cache_data[0]
                last_update = cache_data[1]

                self.logger.info(f"Cached IPs: {old_ips}")
                self.logger.info(f"Last Cache Update: {last_update}")

                added = sorted(set(current_ips) - set(old_ips))
                removed = sorted(set(old_ips) - set(current_ips))

                self.logger.info(f"Node Diff, Added: {added} vs Removed: {removed}")

                if np.array_equal(added, removed):
                    self.logger.info("No node changes detected.")
                else:
                    for pg_database_id in self.database_pg_cluster_id_list.split(","):
                        await asyncio.to_thread(self.update_acl, pg_database_id, DATABASE_TYPE_PG, current_ips, removed)

                    for mysql_database_id in self.database_mysql_cluster_id_list.split(","):
                        await asyncio.to_thread(self.update_acl, mysql_database_id, DATABASE_TYPE_MYSQL, current_ips, removed)

                    await asyncio.to_thread(self.k8s.create_or_update_configmap, self.configmap_name, current_ips)

                    self.logger.info(f"Updated IP list cache in {self.configmap_name}")

                self.logger.info(f"Next check in {self.update_interval} seconds.")
                await asyncio.sleep(int(self.update_interval))
                
        except asyncio.CancelledError:
            self.logger.info("sync_loop cancelled.")
            raise

    def update_acl(self, database_cluster_id, database_type, current_ips, removed_ips):
       
        db_acl_ips = self.linode.get_db_allow_list(database_type, database_cluster_id)
        updated_ips = set(db_acl_ips).union(current_ips).difference(removed_ips)
        
        self.logger.info(
            f"DBaaS ACL: {db_acl_ips}. New IPs: {updated_ips}")

        # checking if DBaaS ACL needs to be updated
        if np.array_equal(db_acl_ips, updated_ips) is False:
            self.linode.update_db_allow_list(
                database_type, database_cluster_id, sorted(updated_ips))
        else:
            self.logger.info(
                "No node changes detected. Won't update DBaaS ACL")        

    async def clear_cache(self):
        return self.k8s.try_delete_configmap(
            self.configmap_name)
