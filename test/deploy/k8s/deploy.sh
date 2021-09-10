#!/bin/bash -x 

SCRIPT_DIR=$(dirname $0)

./$SCRIPT_DIR/destroy.sh

kubectl create namespace cortx
kubectl create cm solution-config --from-file=$SCRIPT_DIR/cluster.yaml \
    --from-file=$SCRIPT_DIR/config.yaml --from-literal "node-id=123" --namespace cortx

#kubectl apply -f $SCRIPT_DIR/cortx-cm-machine-id.yml --namespace cortx
kubectl apply -f $SCRIPT_DIR/cortx-pv-config.yml --namespace cortx
kubectl apply -f $SCRIPT_DIR/cortx-pvc-config.yml --namespace cortx
kubectl apply -f $SCRIPT_DIR/cortx-pod-data.yml --namespace cortx

echo "Waiting for the containers to start up..."
sleep 5

kubectl get pods --namespace cortx
kubectl describe pod cortx-data --namespace cortx
kubectl logs cortx-data --container cortx-provisioner --namespace cortx
