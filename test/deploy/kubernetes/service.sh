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

# Create Config Map For Machine-id
kubectl create configmap control-node-id --from-literal=id=9995f539f4f770e2a3fe9e2e615c32a8 --namespace "$NAMESPACE";
kubectl create configmap storage-node1-id --from-literal=id=aaa120a9e051d103c164f605615c32a4 --namespace "$NAMESPACE";
kubectl create configmap storage-node2-id --from-literal=id=bbb340f79047df9bb52fa460615c32a5 --namespace "$NAMESPACE";
kubectl create configmap storage-node3-id --from-literal=id=ccc8700fe6797ed532e311b0615c32a7 --namespace "$NAMESPACE";

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
