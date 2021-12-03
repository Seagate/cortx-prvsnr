#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="default"
TIMEDELAY="5"
REDEFPODS=false

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

function show_usage {
    echo -e "usage: $(basename $0) [-r]"
    echo -e "Where:"
    echo -e "..."
    echo -e " -r: Deploy with redefined Pods architecture"
    exit 1
}

while [ $# -gt 0 ];  do
    case $1 in
    -r )
        REDEFPODS=true
        ;;
    * )
        echo -e "Invalid argument provided : $1"
        show_usage
        exit 1
        ;;
    esac
    shift 1
done

# Delete Storage and Server Deployment Nodes (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    if [ $REDEFPODS = true ]; then
        print_header "Deleting Data and Server Node - $NODE_NAME";
        kubectl delete pod server-$NODE_NAME --namespace "$NAMESPACE" ;
        kubectl delete pod data-$NODE_NAME --namespace "$NAMESPACE" ;
    else
        print_header "Deleting Storage Node - $NODE_NAME";
        kubectl delete pod storage-$NODE_NAME --namespace "$NAMESPACE" ;
    fi
    sleep $TIMEDELAY;
done

# Delete Control Deployment Node (POD)
print_header "Deleting Control Node - Cluster";
kubectl delete pod control-node --namespace "$NAMESPACE" &
sleep $TIMEDELAY;

if [ $REDEFPODS = true ]; then
    # Delete HA Deployment Node (POD)
    print_header "Deleting HA Node - Cluster";
    kubectl delete pod ha-node --namespace "$NAMESPACE" &
    sleep $TIMEDELAY;
fi

# Wait for deletion of Deployment nodes
wait;

# Create Config Map For Machine-id
kubectl create configmap control-node-id --from-literal=id=9995f539f4f770e2a3fe9e2e615c32a8 --namespace "$NAMESPACE";
if [ $REDEFPODS = true ]; then
    kubectl create configmap ha-node-id --from-literal=id=1115f539f4f770e2a3fe9e2e615c32a8 --namespace "$NAMESPACE";
    kubectl create configmap server-node1-id --from-literal=id=ddd120a9e051d103c164f605615c32a4 --namespace "$NAMESPACE";
    kubectl create configmap server-node2-id --from-literal=id=eee340f79047df9bb52fa460615c32a5 --namespace "$NAMESPACE";
    kubectl create configmap server-node3-id --from-literal=id=fff8700fe6797ed532e311b0615c32a7 --namespace "$NAMESPACE";
    kubectl create configmap data-node1-id --from-literal=id=aaa120a9e051d103c164f605615c32a4 --namespace "$NAMESPACE";
    kubectl create configmap data-node2-id --from-literal=id=bbb340f79047df9bb52fa460615c32a5 --namespace "$NAMESPACE";
    kubectl create configmap data-node3-id --from-literal=id=ccc8700fe6797ed532e311b0615c32a7 --namespace "$NAMESPACE";
else
    kubectl create configmap storage-node1-id --from-literal=id=aaa120a9e051d103c164f605615c32a4 --namespace "$NAMESPACE";
    kubectl create configmap storage-node2-id --from-literal=id=bbb340f79047df9bb52fa460615c32a5 --namespace "$NAMESPACE";
    kubectl create configmap storage-node3-id --from-literal=id=ccc8700fe6797ed532e311b0615c32a7 --namespace "$NAMESPACE";
fi

if [ $REDEFPODS = true ]; then
    # Create HA RunTime Node (POD)
    print_header "Creating HA RunTime Node - Cluster";
    kubectl apply -f "$BASEPATH/runtime-pods/components_ha_node.yaml" --namespace "$NAMESPACE";
fi

# Create Control RunTime Node (POD)
print_header "Creating Cotrol RunTime Node - Cluster";
kubectl apply -f "$BASEPATH/runtime-pods/components_control_node.yaml" --namespace "$NAMESPACE";
sleep $TIMEDELAY;
kubectl apply -f "$BASEPATH/external-services/message_service.yaml" --namespace "$NAMESPACE";

if [ $REDEFPODS = true ]; then
    # Create Data RunTime Node (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Data RunTime Node - $NODE_NAME";
        NODE_POD="$BASEPATH/runtime-pods/components_data_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
        sleep $TIMEDELAY;
    done
    # Create Server RunTime Node (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Server RunTime Node - $NODE_NAME";
        NODE_POD="$BASEPATH/runtime-pods/components_server_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
        sleep $TIMEDELAY;
    done
else
    # Create Storage RunTime Node (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Data RunTime Node - $NODE_NAME";
        NODE_POD="$BASEPATH/runtime-pods/components_storage_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
        sleep $TIMEDELAY;
    done
fi

sleep $TIMEDELAY;
echo -e "Monitor All Nodes for Running status...";
kubectl get pods -o wide -n "$NAMESPACE";
exit 0;
