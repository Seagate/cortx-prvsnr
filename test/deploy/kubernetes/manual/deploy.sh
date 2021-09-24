#!/bin/bash
SCRIPT_DIR=$(dirname $0)
MAXNODES="3"
NAMESPACE="cortx"

function print_header {
    echo -e "---------------------------------------------------"
    echo -e "$1"
    echo -e "---------------------------------------------------"
}

#Label Nodes
NODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2)
COUNT=1; 
for NODE in ${NODES[@]}; do
    kubectl label nodes $NODE --overwrite=true node-name=node$COUNT; 
    COUNT=$(($COUNT+1)); 
done

# Create NameSpace
kubectl create namespace $NAMESPACE

# Create ConfigMap
kubectl create configmap solution-config \
    --from-file=$SCRIPT_DIR/solution-config/cluster.yaml \
    --from-file=$SCRIPT_DIR/solution-config/config.yaml \
    --namespace $NAMESPACE

# Create Persistent Volumes and Claims for Local directories
kubectl apply -f $SCRIPT_DIR/persistent-volumes/cortx-config-pv.yaml  --namespace $NAMESPACE
kubectl apply -f $SCRIPT_DIR/volume-claims/cortx-config-pvc.yaml --namespace $NAMESPACE

# Create Persistent Volumes
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volumes - $NODE_NAME"
    NODE_PVOL=$SCRIPT_DIR/persistent-volumes/block_volume_$NODE_NAME.yaml;
    kubectl apply -f $NODE_PVOL --namespace $NAMESPACE;
    sleep 2;
    kubectl get pv --namespace $NAMESPACE | grep $NODE_NAME;
done

# Create Persistent Volume Claims
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volume Claims - $NODE_NAME"
    NODE_PVCS=$SCRIPT_DIR/volume-claims/block_volumeclaim_$NODE_NAME.yaml;
    kubectl apply -f $NODE_PVCS --namespace $NAMESPACE;
    sleep 2;
done

# Create Headless service for each node
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating headless service for - $NODE_NAME"
    NODE_SVC=$SCRIPT_DIR/external-services/headless_storage_$NODE_NAME.yaml;
    kubectl apply -f $NODE_SVC --namespace $NAMESPACE;
    sleep 2;
done

# Deploy Storage POD for each node
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating POD for - $NODE_NAME"
    NODE_POD=$SCRIPT_DIR/provisioner-pods/deployment_storage_$NODE_NAME.yaml;
    kubectl apply -f $NODE_POD --namespace $NAMESPACE;
    sleep 20;
    kubectl get pods --namespace $NAMESPACE;
done

#Create Secretes
kubectl apply -f $SCRIPT_DIR/solution-config/cortx-secret.yml --namespace $NAMESPACE

# Deploy Control POD
kubectl apply -f $SCRIPT_DIR/external-services/headless_control_node.yaml --namespace $NAMESPACE
kubectl apply -f $SCRIPT_DIR/provisioner-pods/deployment_control_node.yaml --namespace $NAMESPACE
sleep 10
kubectl get pods --namespace $NAMESPACE
