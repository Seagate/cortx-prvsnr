#!/bin/bash -x

SCRIPT_DIR=$(dirname $0)

# deploy the PV & PVC for CORTX support bundle

# Create Persistent Volume
kubectl apply -f "$SCRIPT_DIR"/pv.yml
kubectl apply -f "$SCRIPT_DIR"/pv2.yml

# Create a Persistent Volume Claim
kubectl apply -f "$SCRIPT_DIR"/pv-claim.yml
kubectl apply -f "$SCRIPT_DIR"/pv-claim2.yml

echo "Waiting for the containers to start up..."
sleep 5
