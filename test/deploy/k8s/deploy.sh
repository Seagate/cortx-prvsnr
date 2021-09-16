#!/bin/bash -x
SCRIPT_DIR=$(dirname $0)
"$SCRIPT_DIR"/destroy.sh
kubectl create namespace cortx
kubectl create cm solution-config --from-file="$SCRIPT_DIR"/cluster.yaml \
    --from-file="$SCRIPT_DIR"/config.yaml --namespace cortx
#kubectl apply -f "$SCRIPT_DIR"/cortx-cm-machine-id.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-secret.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pv-config.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pvc-config.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-deployment.yml --namespace cortx
echo "Waiting for the containers to start up..."
sleep 5
kubectl describe deployment cortx-provisioner --namespace cortx
kubectl get pods --namespace cortx
pod=$(kubectl get pods --namespace cortx | grep cortx | awk '{print $1;}')
kubectl logs $pod --namespace cortx
