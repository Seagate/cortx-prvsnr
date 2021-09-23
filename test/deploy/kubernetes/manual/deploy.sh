#!/bin/bash
SCRIPT_DIR=$(dirname $0)
MAXNODES="3"
NAMESPACE="cortx"

function print_header {
    echo -e "---------------------------------------------------"
    echo -e "$1"
    echo -e "---------------------------------------------------"
}

# Create NameSpace
kubectl create namespace $NAMESPACE

# Create ConfigMap
kubectl create configmap solution-config \
    --from-file=$SCRIPT_DIR/solution-config/cluster.yaml \
    --from-file=$SCRIPT_DIR/solution-config/config.yaml \
    --namespace $NAMESPACE

#Create Storage Volumes
kubectl apply -f $SCRIPT_DIR/persistent-volumes/cortx-config-pv.yaml  --namespace $NAMESPACE
kubectl apply -f $SCRIPT_DIR/volume-claims/cortx-config-pvc.yaml --namespace $NAMESPACE

# Create Persistent Volumes
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volumes - $NODE_NAME"
    NODE_PVOL=$SCRIPT_DIR/persistent-volumes/device_volume_$NODE_NAME.yaml;
    kubectl apply -f $NODE_PVOL --namespace $NAMESPACE;
    sleep 2;
    kubectl get pv --namespace $NAMESPACE | grep $NODE_NAME;
done

# Create Persistent Volume Claims
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volume Claims - $NODE_NAME"
    NODE_PVCS=$SCRIPT_DIR/volume-claims/device_volumeclaim_$NODE_NAME.yaml;
    kubectl apply -f $NODE_PVCS --namespace $NAMESPACE;
    sleep 2;
done

# Create Headless service for each node
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating headless service for - $NODE_NAME"
    NODE_SVC=$SCRIPT_DIR/external-services/headless_svc_$NODE_NAME.yaml;
    kubectl apply -f $NODE_SVC --namespace $NAMESPACE;
    sleep 2;
done

# Create POD for each node
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating POD for - $NODE_NAME"
    NODE_POD=$SCRIPT_DIR/provisioner-pods/prov_pod_$NODE_NAME.yaml;
    kubectl apply -f $NODE_POD --namespace $NAMESPACE;
    sleep 20;
    kubectl get pods --namespace $NAMESPACE;
done

# Launch controlnode POD
kubectl apply -f $SCRIPT_DIR/external-services/headless_svc_controlnode1.yaml --namespace $NAMESPACE
kubectl apply -f $SCRIPT_DIR/provisioner-pods/controlnode1.yaml --namespace $NAMESPACE
sleep 10
kubectl get pods --namespace $NAMESPACE

