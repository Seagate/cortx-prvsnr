#!/bin/bash

kubectl create namespace halo
kubectl create secret generic configuration-secrets \
  --from-literal=consul_admin_secret=Seagate@123 \
  --from-literal=kafka_admin_secret=Seagate@123 \
  --from-literal=s3_auth_admin_secret=Seagate@123 \
  --from-literal=csm_mgmt_admin_secret=Seagate@123 -n halo

kubectl create secret generic manager-ssl-cert --from-file=/opt/seagate/halo/manager/s3.seagate.com.pem -n halo

kubectl create configmap solution-config --from-file=/opt/seagate/halo/manager/cluster.yaml -n halo

# configure consul
export PATH="/sbin:/bin:/usr/sbin:/usr/bin:/opt/puppetlabs/bin:/usr/local/bin"
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install consul hashicorp/consul --values /opt/seagate/halo/manager/config.yaml -n halo
sleep 50;
kubectl apply -f /opt/seagate/halo/manager/deployment.yaml -n halo
sleep 30;
