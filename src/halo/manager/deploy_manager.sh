#!/bin/bash
set -e;

kubectl create secret generic configuration-secrets \
  --from-literal=consul_admin_secret=Seagate@123 \
  --from-literal=kafka_admin_secret=Seagate@123 \
  --from-literal=s3_auth_admin_secret=Seagate@123 \
  --from-literal=csm_mgmt_admin_secret=Seagate@123

kubectl create secret generic manager-ssl-cert --from-file=/opt/seagate/halo/manager/s3.seagate.com.pem

kubectl create configmap solution-config --from-file=/opt/seagate/halo/manager/cluster.yaml
kubectl apply -f /opt/seagate/halo/manager/deployment.yaml
