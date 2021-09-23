#!/bin/bash
SCRIPT_DIR=$(dirname $0)
MAXNODES="3"
NAMESPACE="cortx"

function print_header {
    echo -e "---------------------------------------------------"
    echo -e "$1"
    echo -e "---------------------------------------------------"
}

# Delete PODs
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Deleting POD for - $NODE_NAME"
    NODE_POD=$SCRIPT_DIR/provisioner-pods/prov_pod_$NODE_NAME.yaml;
    kubectl delete -f $NODE_POD --namespace $NAMESPACE;
    sleep 5;
done

# Delete Headless services
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Deleting headless service for - $NODE_NAME"
    NODE_SVC=$SCRIPT_DIR/external-services/headless_svc_$NODE_NAME.yaml;
    kubectl delete -f $NODE_SVC --namespace $NAMESPACE;
done

# Delete Persistent Volume Claims
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Deleting Persistent Volume Claims - $NODE_NAME"
    NODE_PVCS=$SCRIPT_DIR/volume-claims/device_volumeclaim_$NODE_NAME.yaml;
    kubectl delete -f $NODE_PVCS --namespace $NAMESPACE;
    sleep 2;
done

# Delete Persistent Volumes
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node"$NODE_INDEX;
    print_header "Deleting Persistent Volumes - $NODE_NAME"
    NODE_PVOL=$SCRIPT_DIR/persistent-volumes/device_volume_$NODE_NAME.yaml;
    kubectl delete -f $NODE_PVOL --namespace $NAMESPACE;
    sleep 2;
done
kubectl delete -f $SCRIPT_DIR/volume-claims/cortx-config-pvc.yaml --namespace cortx
kubectl delete -f $SCRIPT_DIR/persistent-volumes/cortx-config-pv.yaml  --namespace cortx
kubectl delete pv --all --grace-period=0 --force --namespace $NAMESPACE

# Delete Config Map
kubectl delete configmap solution-config --namespace cortx

# Delete NameSpace
kubectl delete namespace $NAMESPACE

