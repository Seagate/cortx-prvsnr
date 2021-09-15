#!/bin/bash -x

SCRIPT_DIR=$(dirname $0)

$SCRIPT_DIR/destroy.sh

kubectl create namespace cortx
kubectl create cm cortx-config --from-file=$SCRIPT_DIR/cluster.yaml \
    --from-file=$SCRIPT_DIR/config.yaml --from-literal "machine-id=123" --namespace cortx

#kubectl apply -f $SCRIPT_DIR/cortx-cm-machine-id.yml --namespace cortx
kubectl apply -f $SCRIPT_DIR/cortx-pv-config.yaml --namespace cortx
kubectl apply -f $SCRIPT_DIR/cortx-pvc-config.yaml --namespace cortx
kubectl apply -f $SCRIPT_DIR/cortx-data-pod.yaml --namespace cortx

echo "Waiting for the containers to start up..."
sleep 5

kubectl get pods --namespace cortx
