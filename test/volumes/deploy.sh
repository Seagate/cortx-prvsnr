#!/bin/bash -x

SCRIPT_DIR=$(dirname $0)

kubectl create namespace cortx

kubectl apply -f "$SCRIPT_DIR"/cortx-pv-logs.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pvc-logs.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pv-config.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pvc-config.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pv-shared.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pvc-shared.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-deployment.yml --namespace cortx

echo "Waiting for pod to be up and running"
sleep 10

kubectl get all
