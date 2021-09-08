#!/bin/bash -x 

./destroy.sh

kubectl apply -f cortx-config-map.yml
kubectl apply -f cortx-config-pv.yml
kubectl apply -f cortx-config-pvc.yml
kubectl apply -f cortx-data-pod.yml

echo "Waiting for the containers to start up..."
sleep 5
kubectl get pods
kubectl describe pod cortx-data
kubectl logs cortx-data --container cortx-provisioner
