#!/bin/bash -x
ARG=$2
replicas='echo $ARG | tr -d -c 0-9'
SCRIPT_DIR=$(dirname $0)
"$SCRIPT_DIR"/destroy.sh
kubectl create namespace cortx
kubectl create cm solution-config --from-file="$SCRIPT_DIR"/cluster.yaml \
    --from-file="$SCRIPT_DIR"/config.yaml --namespace cortx

kubectl apply -f "$SCRIPT_DIR"/cortx-secret.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pv-config.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-pvc-config.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-storagenode-statefulset.yml --namespace cortx
kubectl apply -f "$SCRIPT_DIR"/cortx-controlnode-statefulset.yml --namespace cortx
echo "Waiting for the containers to start up..."
sleep 10

kubectl get statefulset control_node --namespace cortx
kubectl get statefulset storage_node --namespace cortx
kubectl get pods --namespace cortx
pods=$(kubectl get pods --namespace cortx | grep -e "control" -e "storage" | awk '{print $1;}')
for pod in $pods
do
    echo "---- $pod ----"
    kubectl logs $pod --namespace cortx
done
