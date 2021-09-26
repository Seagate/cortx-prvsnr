#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="cortx"

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

# Label Nodes
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
    --from-file=$BASEPATH/solution-config/cluster.yaml \
    --from-file=$BASEPATH/solution-config/config.yaml \
    --namespace $NAMESPACE

# Create Secrets
kubectl apply -f $BASEPATH/solution-config/secrets.yaml --namespace $NAMESPACE

# Create Persistent Volumes for Block Devices (PV)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volumes for Block Devices - $NODE_NAME"
    NODE_BDEV=$BASEPATH/persistent-volumes/block_devices_$NODE_NAME.yaml;
    kubectl apply -f $NODE_BDEV --namespace $NAMESPACE;
    sleep 2;
    kubectl get pv --namespace $NAMESPACE | grep $NODE_NAME;
done

# Create Persistent Volume Claims for Block Devices (PVC)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volume Claims for Block Devices - $NODE_NAME"
    NODE_BVOL=$BASEPATH/volume-claims/block_volumes_$NODE_NAME.yaml;
    kubectl apply -f $NODE_BVOL --namespace $NAMESPACE;
    sleep 2;
done

# Create Persistent Volumes for Storage Devices (PV)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volumes for Storage Devices - $NODE_NAME"
    NODE_SDEV=$BASEPATH/persistent-volumes/storage_devices_$NODE_NAME.yaml;
    kubectl apply -f $NODE_SDEV --namespace $NAMESPACE;
    sleep 2;
    kubectl get pv --namespace $NAMESPACE | grep $NODE_NAME;
done

# Create Persistent Volume Claims for Storage Devices (PVC)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Persistent Volume Claims for Storage Devices - $NODE_NAME"
    NODE_SVOL=$BASEPATH/volume-claims/storage_volumes_$NODE_NAME.yaml;
    kubectl apply -f $NODE_SVOL --namespace $NAMESPACE;
    sleep 2;
done

# Create Control Service (Headless)
print_header "Creating Cotrol Service - Cluster"
kubectl apply -f $BASEPATH/external-services/headless_control_node.yaml --namespace $NAMESPACE

# Create Control Node (POD)
print_header "Creating Cotrol Node - Cluster"
kubectl apply -f $BASEPATH/provisioner-pods/deployment_control_node.yaml --namespace $NAMESPACE

# Create Storage Service (Headless)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Storage Service - $NODE_NAME"
    NODE_SVC=$BASEPATH/external-services/headless_storage_$NODE_NAME.yaml;
    kubectl apply -f $NODE_SVC --namespace $NAMESPACE;
    sleep 2;
done

# Create Storage Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Creating Storage Node - $NODE_NAME"
    NODE_POD=$BASEPATH/provisioner-pods/deployment_storage_$NODE_NAME.yaml;
    kubectl apply -f $NODE_POD --namespace $NAMESPACE;
    sleep 2;
done

sleep 10
kubectl get pods --namespace $NAMESPACE
