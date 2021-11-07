#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="default"
TIMEDELAY="5"
INTRDELAY="2"
UPGRADE_IMAGE="ghcr.io/seagate/cortx-all:2.0.0-401-RC3.6"

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

# Create Upgrade Control POD
print_header "Creating Upgrade Control Node - Cluster";
kubectl apply -f "$BASEPATH/upgrade-pods/upgrade_control_node.yaml" --namespace "$NAMESPACE";

# Wait for Upgrade Control-POD execution
printf "\nWaiting for Upgrade Control Node.";
while [ "$(kubectl get pods | grep -E "(^|\s)control-node($|\s)" | awk '{print $3}')" != "Completed" ]; do
    printf ".";
    sleep $TIMEDELAY;
done
printf "\n";


# Create Upgrade Storage POD
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Creating Upgrade Storage Node - $NODE_NAME";
    NODE_POD="$BASEPATH/upgrade-pods/upgrade_storage_$NODE_NAME.yaml";
    kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
    sleep $TIMEDELAY;
done

# Wait for Upgrade Storage-POD execution
printf "\nWaiting for Upgrade Storage Node.";
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="storage-node$NODE_INDEX";
    while [ "$(kubectl get pods | grep -E "(^|\s)$NODE_NAME($|\s)" | awk '{print $3}')" != "Completed" ]; do
        printf ".";
        sleep $TIMEDELAY;
    done
done
printf "\n";

# Delete Upgrade Storage RunTime Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Storage Node - $NODE_NAME";
    kubectl delete pod storage-$NODE_NAME --namespace "$NAMESPACE" &
    sleep $TIMEDELAY;
done

# Delete Upgrade Control RunTime Node (POD)
print_header "Deleting Control Node - Cluster";
kubectl delete pod control-node --namespace "$NAMESPACE" &
sleep $TIMEDELAY;

# Wait for delete Upgrade control/storage nodes
wait;

# Upgrade Runtime Storage POD
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="storage-node$NODE_INDEX";
    kubectl set image deployment $NODE_NAME cortx-hax=$UPGRADE_IMAGE cortx-confd=$UPGRADE_IMAGE cortx-ios1=$UPGRADE_IMAGE cortx-ios2=$UPGRADE_IMAGE cortx-s31=$UPGRADE_IMAGE  cortx-s32=$UPGRADE_IMAGE cortx-s3auth=$UPGRADE_IMAGE  cortx-s3haproxy=$UPGRADE_IMAGE cortx-s3bgc=$UPGRADE_IMAGE
    sleep $TIMEDELAY;
done

# Upgrade Runtime Control POD
kubectl set image deployment control-node csm-agent=$UPGRADE_IMAGE s3-bg-producer=$UPGRADE_IMAGE

