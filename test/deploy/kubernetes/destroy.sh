#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="default"
DEF3PLOGS="/tmp/3rdparty_services_destroy.log"
INTRDELAY="2"

function print_header {
    echo "--------------------------------------------------------------------------"
    echo -e "$1"
    echo "--------------------------------------------------------------------------"
}

# Delete Storage Node Service (Headless)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Storage Service - $NODE_NAME";
    NODE_SVC="$BASEPATH/external-services/headless_data_$NODE_NAME.yaml";
    kubectl delete -f "$NODE_SVC" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Delete Server Node Service (Headless)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Server-Node Service - $NODE_NAME";
    NODE_SVC="$BASEPATH/external-services/headless_server_$NODE_NAME.yaml";
    kubectl delete -f "$NODE_SVC" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Delete Storage/Data Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Storage Node - $NODE_NAME";
    kubectl delete deployment data-$NODE_NAME --namespace "$NAMESPACE" ;
    kubectl delete deployment storage-$NODE_NAME --namespace "$NAMESPACE" ;

    sleep $INTRDELAY;
done
wait;

# Delete Server Node Service (Headless)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Server-Node Service - $NODE_NAME";
    NODE_SVC="$BASEPATH/external-services/headless_server_$NODE_NAME.yaml";
    kubectl delete -f "$NODE_SVC" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Delete Server Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Server Node - $NODE_NAME";
    kubectl delete deployment server-$NODE_NAME --namespace "$NAMESPACE" ;
    sleep $INTRDELAY;
done
wait;

# Delete Control Node Service (Headless)
print_header "Deleting Control Service - Cluster";
kubectl delete -f "$BASEPATH/external-services/headless_control_node.yaml" --namespace "$NAMESPACE";

# Delete Control Node (POD)
print_header "Deleting Control Node - Cluster";
kubectl delete deployment control-node --namespace "$NAMESPACE";
sleep $INTRDELAY;

# Delete Ha Node Service (Headless)
print_header "Deleting Ha Node Service - Cluster";
kubectl delete -f "$BASEPATH/external-services/headless_ha_node.yaml" --namespace "$NAMESPACE";
kubectl delete -f "$BASEPATH/external-services/cluster_role.yaml" --namespace "$NAMESPACE";
kubectl delete -f "$BASEPATH/external-services/cluster_role_binding.yaml" --namespace "$NAMESPACE";
kubectl delete -f "$BASEPATH/external-services/service_account.yaml" --namespace "$NAMESPACE";

# Delete HA Node (POD)
print_header "Deleting HA Node - Cluster";
kubectl delete deployment ha-node --namespace "$NAMESPACE";
sleep $INTRDELAY;

# Delete Persistent Volume Claims for Block Devices (PVC)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Persistent Volume Claims for Block Devices - $NODE_NAME";
    NODE_BVOL="$BASEPATH/volume-claims/block_volumes_$NODE_NAME.yaml";
    kubectl delete -f "$NODE_BVOL" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Delete Persistent Volumes for Block Devices (PV)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Persistent Volumes for Block Devices - $NODE_NAME";
    NODE_BDEV="$BASEPATH/persistent-volumes/block_devices_$NODE_NAME.yaml";
    kubectl delete -f "$NODE_BDEV" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Delete Persistent Volume Claims for Storage Devices (PVC)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Persistent Volume Claims for Storage Devices - $NODE_NAME";
    NODE_SVOL="$BASEPATH/volume-claims/storage_volumes_$NODE_NAME.yaml";
    kubectl delete -f "$NODE_SVOL" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Delete Persistent Volumes for Storage Devices (PV)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Persistent Volumes for Storage Devices - $NODE_NAME";
    NODE_SDEV="$BASEPATH/persistent-volumes/storage_devices_$NODE_NAME.yaml";
    kubectl delete -f "$NODE_SDEV" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Uninstall 3rdParty Services
./3rdparty-services/destroy_components.sh > $DEF3PLOGS 2>&1;

# Remove remaining PVC
kubectl delete pvc --all --force --namespace "$NAMESPACE";
kubectl get pvc --namespace "$NAMESPACE" | grep "$NODE_NAME";

# Remove remaining PV
kubectl delete pv --all --force --namespace "$NAMESPACE";
kubectl get pv --namespace "$NAMESPACE" | grep "$NODE_NAME";

# Delete Secrets
kubectl delete -f "$BASEPATH/solution-config/secrets.yaml" --namespace "$NAMESPACE";

# Delete Config Map
kubectl delete configmap solution-config --namespace "$NAMESPACE";
kubectl delete configmap control-node-id --namespace "$NAMESPACE";
kubectl delete configmap ha-node-id --namespace "$NAMESPACE";
for NODE_INDEX in $(seq 1 $MAXNODES); do
    DATA_NODE="data-node$NODE_INDEX-id";
    SERVER_NODE="server-node$NODE_INDEX-id"
    STORAGE_NODE="storage-node$NODE_INDEX-id"
    kubectl delete configmap $DATA_NODE --namespace "$NAMESPACE";
    kubectl delete configmap $SERVER_NODE --namespace "$NAMESPACE";
    kubectl delete configmap $STORAGE_NODE --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Delete non-default namespace
if [[ "$NAMESPACE" != "default" ]]; then
    kubectl delete namespace $NAMESPACE;
fi

# Validate no resources in Namespace
kubectl delete all --all --namespace "$NAMESPACE";
kubectl get all --namespace "$NAMESPACE";
exit 0;
