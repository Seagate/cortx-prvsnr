#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="default"
TIMEDELAY="10"
FAILED='\033[0;31m'       #RED
PASSED='\033[0;32m'       #GREEN
ALERT='\033[0;33m'        #YELLOW
INFO='\033[0;36m'        #CYAN
NC='\033[0m'              #NO COLOUR
num_pods=$(($MAXNODES+1))
count=0

function show_usage {
    echo -e "usage: $(basename $0) [-i UPGRADE-IMAGE]"
    echo -e "Where:"
    echo -e "..."
    echo -e " UPGARDE-IMAGE : Image TAG To be Provided for Software Upgrade"
    exit 1
}

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

while [ $# -gt 0 ];  do
    case $1 in
    -i )
        shift 1
        UPGRADE_IMAGE=$1
        ;;
    * )
        echo -e "Invalid argument provided : $1"
        show_usage
        exit 1
        ;;
    esac
    shift 1
done

[ -z $UPGRADE_IMAGE ] && echo -e "ERROR: Missing Upgrade Image tag. Please Provide Image TAG for Upgrade" && show_usage

# Validate if All Pods are running
printf "${INFO}| Checking Pods |${NC}\n"
while IFS= read -r line; do
    IFS=" " read -r -a status <<< "$line"
    IFS="/" read -r -a ready_status <<< "${status[1]}"
    if [[ "${status[0]}" != "" ]]; then
        printf "${status[0]}..."
        if [[ "${status[2]}" != "Running" || "${ready_status[0]}" != "${ready_status[1]}" ]]; then
            printf "${FAILED}FAILED${NC}\n"
        else
            printf "${PASSED}PASSED${NC}\n"
            count=$((count+1))
        fi
    fi
done <<< "$(kubectl get pods --namespace=$namespace | grep 'storage\|control')"

if [[ $num_pods -eq $count ]]; then
    printf "OVERALL STATUS: ${PASSED}PASSED${NC}\n"
else
    printf "OVERALL STATUS: ${FAILED}FAILED${NC}\n"
fi

# Validate if all CORTX Cluster services are online
torage_pod=$(kubectl get pods | grep 'storage' | awk 'FNR==1 {print $1}')
cluster_status=$(kubectl exec -it "$storage_pod" -c cortx-hax -- bash -c "hctl status | grep 'offline'")
if [ ! -z "$cluster_status" -a "$cluster_status" != " " ]; then
        echo "ERROR: Some CORTX Cluster services are in offline state, Upgrade cannot be performed on UnHealthy Cluster"
fi

# Update Image in Upgrade PODs
print_header "Updating Upgrade image in Upgrade Pods - Cluster";
sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$UPGRADE_IMAGE'!' $BASEPATH/upgrade-pods/upgrade_control_node.yaml
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    NODE_POD="$BASEPATH/upgrade-pods/upgrade_storage_$NODE_NAME.yaml";
    sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$UPGRADE_IMAGE'!' $NODE_POD;
done

# Upgrade Runtime Storage POD's
for NODE_INDEX in $(seq 1 $MAXNODES); do
    # Pause Runtime Storage POD
    STORAGE_NODE="storage-node$NODE_INDEX";
    NODE_NAME="node$NODE_INDEX";
    print_header "Pausing Runtime Storage Node $STORAGE_NODE";
    kubectl rollout pause deployment $STORAGE_NODE;

    # Create Upgrade Storage POD
    print_header "Creating Upgrade Storage Node - $NODE_NAME";
    NODE_POD="$BASEPATH/upgrade-pods/upgrade_storage_$NODE_NAME.yaml";
    kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";

    # Wait for Upgrade Storage-POD execution
    printf "\nWaiting for Upgrade Storage Node $NODE_NAME";
    while [ "$(kubectl get pods | grep -E "(^|\s)$STORAGE_NODE($|\s)" | awk '{print $3}')" != "Completed" ]; do
        printf ".";
    done

    # Upgrade Runtime POD for each node
    print_header "Upgrading Runtime Storage Node for - $NODE_NAME";
    kubectl set image deployment $STORAGE_NODE cortx-hax=$UPGRADE_IMAGE cortx-confd=$UPGRADE_IMAGE cortx-ios1=$UPGRADE_IMAGE cortx-ios2=$UPGRADE_IMAGE cortx-s31=$UPGRADE_IMAGE  cortx-s32=$UPGRADE_IMAGE cortx-s3auth=$UPGRADE_IMAGE  cortx-s3haproxy=$UPGRADE_IMAGE cortx-s3bgc=$UPGRADE_IMAGE;

    # Resume Runtime Storage
    print_header "Resuming Runtime Storage Node - Cluster";
    kubectl rollout resume deployment $STORAGE_NODE;
    sleep $TIMEDELAY;

done

# Pause Runtime Control POD
print_header "Pausing Runtime Control Node - Cluster";
kubectl rollout pause deployment control-node

# Create Upgrade Control POD
print_header "Creating Upgrade Control Node - Cluster";
kubectl apply -f "$BASEPATH/upgrade-pods/upgrade_control_node.yaml" --namespace "$NAMESPACE";

# Wait for Upgrade Control-POD execution
printf "\nWaiting for Upgrade Control Node.";
while [ "$(kubectl get pods | grep -E "(^|\s)control-node($|\s)" | awk '{print $3}')" != "Completed" ]; do
    printf ".";
done
printf "\n";

# Upgrade Runtime Control POD
kubectl set image deployment control-node csm-agent=$UPGRADE_IMAGE s3-bg-producer=$UPGRADE_IMAGE

# Resume Runtime Control POD
print_header "Resuming Runtime Control Node - Cluster";
kubectl rollout resume deployment control-node
sleep $TIMEDELAY;

# Delete Upgrade Storage RunTime Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    print_header "Deleting Storage Node - $NODE_NAME";
    kubectl delete pod storage-$NODE_NAME --namespace "$NAMESPACE" &
    sleep $TIMEDELAY;
done

# Delete Upgrade Control Node (POD)
print_header "Deleting Control Node - Cluster";
kubectl delete pod control-node --namespace "$NAMESPACE" &
sleep $TIMEDELAY;

# Wait for delete Upgrade control/storage nodes
wait;


