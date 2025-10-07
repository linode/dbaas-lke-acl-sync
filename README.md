# LKE DBaaS ACL Syncer Demo
### THIS REPO IS FOR DEMONSTRATION PURPOSES ##

A service that add LKE node IP addresses t the allow list for a given of list of Linode Managed Database (PostgreSQL or MySQL) clusters.

## Features

- Lists LKE nodes frequently and get a list of IP addresses
- Updates `allow_list` in Linode Managed Database
- Stores current state in a Kubernetes ConfigMap for tracking
- Exposes a `/health` endpoint for monitoring
- Exposes a `/force-next-update` endpoint to force updating
- Built with FastAPI and Kubernetes Python client

## Environment Variables
### Required:
| Name                        | Description                                           |
|-----------------------------|-------------------------------------------------------|
| `LINODE_API_KEY`            | Linode personal access token                          |
| `DATABASE_PG_CLUSTER_IDS`   | ID of your Linode Managed DB cluster                  |
| `DATABASE_MYSQL_CLUSTER_IDS`| `postgresql` or `mysql`                               |



### Optional:
| Name                  | Description                                           |
|-----------------------|-------------------------------------------------------|
| `NODES_CONFIGMAP_NAME`| The name of the configmap to store list of current    |
|                       | addresses. (default: "lke-node-ips")                  |
| `NAMESPACE`           | The namespace for the configmap to store list of      |
|                       | current addresses. (default: "default")               |
| `LOG_LEVEL`           | Logging level (`DEBUG`, `INFO`, etc.)                 |


## Running Locally

```bash
pip install -r requirements.txt
fastapi run app/main.py --port 8000
```

## Docker
```bash
docker build -t lke-dbaas-acl-sync-service:latest .
docker run -p 8000:8000 \
        --env-file .env \
        -v ~/.kube/config:/etc/kubeconfig \
        -e KUBECONFIG=/etc/kubeconfig \
        --name lke-dbaas-acl-sync-service \
        lke-dbaas-acl-sync-service:latest
```

## Kubernetes
```bash
./install.sh
```
