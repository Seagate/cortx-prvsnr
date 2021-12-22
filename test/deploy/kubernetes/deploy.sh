#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="default"
TIMEDELAY="5"
INTRDELAY="2"
DEF3PLOGS="/tmp/3rdparty_services_install.log"
REDEFPODS=false

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

function show_usage {
    echo -e "usage: $(basename $0) [-i] [-r]"
    echo -e "Where:"
    echo -e "..."
    echo -e "-i : Deploy specified Cortx Image"
    echo -e "-r : Deploy with redefined Pods architecture"
    exit 1
}

function wait_for_pod_to_be_ready(){
    while true; do
        count=0
        while IFS= read -r line; do
            IFS=" " read -r -a pod_status <<< "$line"
            IFS="/" read -r -a ready_status <<< "${pod_status[1]}"
            if [[ "${pod_status[2]}" != "Running" || "${ready_status[0]}" != "${ready_status[1]}" ]]; then
                if [[ "${pod_status[2]}" == "Error" ]]; then
                    printf "\n'${pod_status[0]}' pod deployment did not complete. Exit early.\n"
                    exit 1
                fi
                break
            fi
            count=$((count+1))
        done <<< "$(kubectl get pods --namespace=$namespace | grep  $1)"

        if [[ $MAXNODES -eq $count ]]; then
            break
        else
            printf "."
        fi
        sleep 1s
    done
}

while [ $# -gt 0 ];  do
    case $1 in
    -i )
        shift 1
        DEPLOY_IMAGE=$1
        ;;
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
[ -z $DEPLOY_IMAGE ] && echo -e "ERROR: Missing Deploy Image Argument. Please Provide Image TAG.." && show_usage

# Update Image in All PODs
print_header "Updating Image in All Pods - Cluster";
sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$DEPLOY_IMAGE'!' $BASEPATH/runtime-pods/components_control_node.yaml
if [ $REDEFPODS = true ]; then
    sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$DEPLOY_IMAGE'!' $BASEPATH/runtime-pods/components_ha_node.yaml
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        DATA_RUNTIME_POD="$BASEPATH/runtime-pods/components_data_$NODE_NAME.yaml";
        SERVER_RUNTIME_POD="$BASEPATH/runtime-pods/components_server_$NODE_NAME.yaml";
        sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$DEPLOY_IMAGE'!' $DATA_RUNTIME_POD;
        sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$DEPLOY_IMAGE'!' $SERVER_RUNTIME_POD;
    done
else
    for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    STORAGE_RUNTIME_POD="$BASEPATH/runtime-pods/components_storage_$NODE_NAME.yaml";
    sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$DEPLOY_IMAGE'!' $STORAGE_RUNTIME_POD;
    done
fi

# Label Nodes
NODES=$(kubectl get nodes | tail -n+2 | sort -k3 | awk '{print $1}')
COUNT=1;
for NODE in ${NODES[@]}; do
    kubectl label nodes "$NODE" --overwrite=true node-name=node$COUNT;
    COUNT=$((COUNT+1));
done

# Create non-default namespace
if [[ "$NAMESPACE" != "default" ]]; then
    kubectl create namespace $NAMESPACE;
fi

# Install 3rdParty Services
print_header "Configuring 3rdParty Services";
./3rdparty-services/deploy_components.sh > $DEF3PLOGS 2>&1;
kubectl get service --namespace $NAMESPACE;

if [ $REDEFPODS = true ]; then
    cp "$BASEPATH"/template-config/cluster_redefined.yaml "$BASEPATH"/solution-config/cluster.yaml;
else
    cp "$BASEPATH"/template-config/cluster_default.yaml "$BASEPATH"/solution-config/cluster.yaml;
fi

# Create ConfigMap
kubectl create configmap solution-config \
    --from-file="$BASEPATH"/solution-config/cluster.yaml \
    --from-file="$BASEPATH"/solution-config/config.yaml \
    --namespace "$NAMESPACE";

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


# Create Secrets
kubectl apply -f "$BASEPATH"/solution-config/secrets.yaml --namespace $NAMESPACE;

# Create Persistent Volumes for Block Devices (PV)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Creating Persistent Volumes for Block Devices - $NODE_NAME";
    NODE_BDEV="$BASEPATH/persistent-volumes/block_devices_$NODE_NAME.yaml";
    kubectl apply -f "$NODE_BDEV" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
    kubectl get pv --namespace "$NAMESPACE" | grep "$NODE_NAME";
done

# Create Persistent Volume Claims for Block Devices (PVC)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Creating Persistent Volume Claims for Block Devices - $NODE_NAME";
    NODE_BVOL="$BASEPATH/volume-claims/block_volumes_$NODE_NAME.yaml";
    kubectl apply -f "$NODE_BVOL" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Create Persistent Volumes for Storage Devices (PV)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Creating Persistent Volumes for Storage Devices - $NODE_NAME";
    NODE_SDEV="$BASEPATH/persistent-volumes/storage_devices_$NODE_NAME.yaml";
    kubectl apply -f "$NODE_SDEV" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
    kubectl get pv --namespace "$NAMESPACE" | grep "$NODE_NAME";
done

# Create Persistent Volume Claims for Storage Devices (PVC)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Creating Persistent Volume Claims for Storage Devices - $NODE_NAME";
    NODE_SVOL="$BASEPATH/volume-claims/storage_volumes_$NODE_NAME.yaml";
    kubectl apply -f "$NODE_SVOL" --namespace "$NAMESPACE";
    sleep $INTRDELAY;
done

# Create Control Node Service (Headless)
print_header "Creating Cotrol Service - Cluster";
kubectl apply -f "$BASEPATH/external-services/headless_control_node.yaml" --namespace "$NAMESPACE";

# Create Control Node (POD)
print_header "Creating Cotrol Node - Cluster";
kubectl apply -f "$BASEPATH/runtime-pods/components_control_node.yaml" --namespace "$NAMESPACE";

# Wait for Control-Node (POD) execution
printf "\nWaiting for Control Node.";
while [ "$(kubectl get pods | grep control-node | awk '{print $3}')" != "Running" ]; do
    if [ "$(kubectl get pods | grep control-node | awk '{print $3}')" == "Error" ]; then
        printf "\n' control-node pod deployment did not complete. Exit early.\n"
        exit 1
    fi
    printf ".";
    sleep $TIMEDELAY;
done
printf "\n";

if [ $REDEFPODS = true ]; then
    # Create HA Node Service (Headless)
    print_header "Creating HA Node Service - Cluster";
    kubectl apply -f "$BASEPATH/external-services/headless_ha_node.yaml" --namespace "$NAMESPACE";

    # Create HA Node Cluster services and service account
    print_header "Creating Cluster Role and Custer Role binding service - Cluster";
    kubectl create -f "$BASEPATH/external-services/cluster_role.yaml" --namespace "$NAMESPACE";
    kubectl create -f "$BASEPATH/external-services/cluster_role_binding.yaml" --namespace "$NAMESPACE";

    # Create Service Account (HA Node)
    print_header "Creating Service account for HA";
    kubectl create -f "$BASEPATH/external-services/service_account.yaml" --namespace "$NAMESPACE";

    # Create HA Node (POD)
    print_header "Creating HA Node - Cluster";
    kubectl apply -f "$BASEPATH/runtime-pods/components_ha_node.yaml" --namespace "$NAMESPACE";

    # Wait for HA Node (POD) execution
    printf "\nWaiting for HA Node.";
    while [ "$(kubectl get pods | grep ha-node | awk '{print $3}')" != "Running" ]; do
        if [ "$(kubectl get pods | grep ha-node | awk '{print $3}')" == "Error" ]; then
            printf "\n ha-node pod deployment did not complete. Exit early.\n"
            exit 1
        fi
        printf ".";
        sleep $TIMEDELAY;
    done
    printf "\n";

    # Create Data-Node Service (Headless)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Data Node Service - $NODE_NAME";
        NODE_SVC="$BASEPATH/external-services/headless_data_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_SVC" --namespace "$NAMESPACE";
        sleep $INTRDELAY;
    done

    # Create Data Node (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Data Node - $NODE_NAME";
        NODE_POD="$BASEPATH/runtime-pods/components_data_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
        sleep $TIMEDELAY;
    done
    printf "\nWaiting for Data pod to be ready."
    wait_for_pod_to_be_ready 'data-node.-.*'
    printf "\n\n"

    # Create Server Node Service (Headless)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Server Node Service - $NODE_NAME";
        NODE_SVC="$BASEPATH/external-services/headless_server_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_SVC" --namespace "$NAMESPACE";
        sleep $INTRDELAY;
    done

    # Create Server Node (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Server Node - $NODE_NAME";
        NODE_POD="$BASEPATH/runtime-pods/components_server_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
        sleep $TIMEDELAY;
    done
    printf "\nWaiting for Server pod to be ready."
    wait_for_pod_to_be_ready 'server-node.-.*'
    printf "\n\n"

else
    # Create Storage Node Service (Headless)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Storage Service - $NODE_NAME";
        NODE_SVC="$BASEPATH/external-services/headless_storage_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_SVC" --namespace "$NAMESPACE";
        sleep $INTRDELAY;
    done

    # Create Storage Node (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        print_header "Creating Storage Node - $NODE_NAME";
        NODE_POD="$BASEPATH/runtime-pods/components_storage_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";
        sleep $TIMEDELAY;
    done
    printf "\nWaiting for Storage pod to be ready."
    wait_for_pod_to_be_ready 'storage-node.-.*'
    printf "\n\n"
fi

echo -e "Monitor All Nodes for Completed status";
kubectl get pods -o wide -n "$NAMESPACE";
exit 0;
