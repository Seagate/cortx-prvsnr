#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="default"
TIMEDELAY="5"

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

# Delete Storage RunTime Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Storage Node - $NODE_NAME";
    kubectl delete pod storage-$NODE_NAME --namespace "$NAMESPACE" &
    sleep $TIMEDELAY;
done

# Delete Control RunTime Node (POD)
print_header "Deleting Control Node - Cluster";
kubectl delete pod control-node --namespace "$NAMESPACE" &
sleep $TIMEDELAY;

# Wait for delete control/storage nodes
wait;

# Create Control RunTime Node (POD)
print_header "Creating Cotrol RunTime Node - Cluster";
kubectl apply -f "$BASEPATH/runtime-pods/components_control_node.yaml" --namespace "$NAMESPACE";

# Create Storage RunTime Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Creating Storage RunTime Node - $NODE_NAME";
    NODE_POD="$BASEPATH/runtime-pods/components_storage_$NODE_NAME.yaml";
    kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
    sleep $TIMEDELAY;
done

sleep $TIMEDELAY;
echo -e "Monitor Storage/Control Nodes for Running status...";
kubectl get pods -o wide -n "$NAMESPACE";
exit 0;
