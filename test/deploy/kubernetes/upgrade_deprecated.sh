#!/bin/bash
BASEPATH=$(dirname $0)
MAXNODES=$(kubectl get nodes | awk -v col=1 '{print $col}' | tail -n+2 | wc -l)
NAMESPACE="default"
TIMEDELAY="30"
FAILED='\033[0;31m'       #RED
PASSED='\033[0;32m'       #GREEN
INFO='\033[0;36m'        #CYAN
NC='\033[0m'              #NO COLOUR
REDEFPODS=false
UPGRADEPIDFILE=/var/run/upgrade.sh.pid

#check if file exits with pid in it. Throw error if PID is present
if [ -s "$UPGRADEPIDFILE" ]; then
   echo "Upgrade is already being performed on the cluster."
   exit 1
fi

# Create a file with current PID to indicate that process is running.
echo $$ > "$UPGRADEPIDFILE"

function show_usage {
    echo -e "usage: $(basename $0) [-i UPGRADE-IMAGE]"
    echo -e "Where:"
    echo -e "..."
    echo -e "-i : Upgrade With specified Cortx Image"
    echo -e "-r : Upgrade redefined Pods architecture"
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

[ -z $UPGRADE_IMAGE ] && echo -e "ERROR: Missing Upgrade Image tag. Please Provide Image TAG for Upgrade" && show_usage

# Validate if All Pods are running
printf "${INFO}| Checking Pods Status |${NC}\n"
while IFS= read -r line; do
    IFS=" " read -r -a status <<< "$line"
    IFS="/" read -r -a ready_status <<< "${status[1]}"
    if [[ "${status[0]}" != "" ]]; then
        printf "${status[0]}..."
        if [[ "${status[2]}" != "Running" || "${ready_status[0]}" != "${ready_status[1]}" ]]; then
            printf "${FAILED}FAILED${NC}\n"
            exit 1;
        else
            printf "${PASSED}PASSED${NC}\n"
        fi
    fi
done <<< "$(kubectl get pods --namespace=$namespace | grep 'data-node.-*.\|control-node-.*\|server-node.-.*\|ha-node-.*\|storage-node.-.*')"

# Update Image in Upgrade PODs
print_header "Updating image using Upgrade Pods - Cluster";
sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$UPGRADE_IMAGE'!' $BASEPATH/upgrade-pods/upgrade_control_node.yaml
if [ $REDEFPODS = true ]; then
    sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$UPGRADE_IMAGE'!' $BASEPATH/upgrade-pods/upgrade_ha_node.yaml
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        NODE_NAME="node$NODE_INDEX";
        DATA_POD="$BASEPATH/upgrade-pods/upgrade_data_$NODE_NAME.yaml";
        SERVER_POD="$BASEPATH/upgrade-pods/upgrade_server_$NODE_NAME.yaml";
        sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$UPGRADE_IMAGE'!' $DATA_POD;
        sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$UPGRADE_IMAGE'!' $SERVER_POD;
    done
else
    for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    STORAGE_POD="$BASEPATH/upgrade-pods/upgrade_storage_$NODE_NAME.yaml";
    sed -i -e 's!^\(\s*image:\)[^"]*!\1 '$UPGRADE_IMAGE'!' $STORAGE_POD;
    done
fi

if [ $REDEFPODS = true ]; then
    # Upgrade Runtime DATA Nodes (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        # Pause Runtime Data Node (POD)
        DATA_NODE="data-node$NODE_INDEX";
        NODE_NAME="node$NODE_INDEX";
        print_header "Pausing Runtime Data Node $DATA_NODE";
        kubectl rollout pause deployment $DATA_NODE;

        # Create Upgrade Data Node (POD)
        print_header "Creating Upgrade Data Node - $NODE_NAME";
        NODE_POD="$BASEPATH/upgrade-pods/upgrade_data_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";

        # Wait for Upgrade Data Node execution (POD)
        printf "\nWaiting for Upgrade Data Node $NODE_NAME";
        while [ "$(kubectl get pods | grep -E "(^|\s)$DATA_NODE($|\s)" | awk '{print $3}')" != "Completed" ]; do
            printf ".";
        done

        # Upgrade Runtime Data Node (POD)
        print_header "Upgrading Runtime Data Node for - $NODE_NAME";
        kubectl set image deployment $DATA_NODE cortx-hax=$UPGRADE_IMAGE cortx-confd=$UPGRADE_IMAGE cortx-ios1=$UPGRADE_IMAGE cortx-ios2=$UPGRADE_IMAGE ;
    
        # Resume Runtime Data Node (POD)
        print_header "Resuming Runtime Data Node - Cluster";
        kubectl rollout resume deployment $DATA_NODE;
        sleep $TIMEDELAY;
    done

    # Upgrade Runtime Server Node (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        # Pause Runtime Server Node (POD)
        SERVER_NODE="server-node$NODE_INDEX";
        NODE_NAME="node$NODE_INDEX";
        print_header "Pausing Runtime Server Node $DATA_NODE";
        kubectl rollout pause deployment $SERVER_NODE;

        # Create Upgrade Server Node (POD)
        print_header "Creating Upgrade Server Node - $NODE_NAME";
        NODE_POD="$BASEPATH/upgrade-pods/upgrade_server_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";

        # Wait for Upgrade Server Node execution (POD)
        printf "\nWaiting for Upgrade Server Node $NODE_NAME";
        while [ "$(kubectl get pods | grep -E "(^|\s)$SERVER_NODE($|\s)" | awk '{print $3}')" != "Completed" ]; do
            printf ".";
        done

        # Upgrade Runtime Server Node (POD)
        print_header "Upgrading Runtime Server Node for - $NODE_NAME";
        kubectl set image deployment $SERVER_NODE cortx-s31=$UPGRADE_IMAGE  cortx-s32=$UPGRADE_IMAGE cortx-s3auth=$UPGRADE_IMAGE  cortx-s3haproxy=$UPGRADE_IMAGE cortx-s3bgc=$UPGRADE_IMAGE;

        # Resume Runtime Server Node (POD)
        print_header "Resuming Runtime Server Node - Cluster";
        kubectl rollout resume deployment $SERVER_NODE;
        sleep $TIMEDELAY;
    done
else
    # Upgrade Runtime Storage Nodes (POD)
    for NODE_INDEX in $(seq 1 $MAXNODES); do
        # Pause Runtime Storage Node (POD)
        STORAGE_NODE="storage-node$NODE_INDEX";
        NODE_NAME="node$NODE_INDEX";
        print_header "Pausing Runtime Storage Node $STORAGE_NODE";
        kubectl rollout pause deployment $STORAGE_NODE;

        # Create Upgrade Storage Node (POD)
        print_header "Creating Upgrade Storage Node - $NODE_NAME";
        NODE_POD="$BASEPATH/upgrade-pods/upgrade_storage_$NODE_NAME.yaml";
        kubectl apply -f "$NODE_POD" --namespace "$NAMESPACE";

        # Wait for Upgrade Storage Node execution (POD)
        printf "\nWaiting for Upgrade Storage Node $NODE_NAME";
        while [ "$(kubectl get pods | grep -E "(^|\s)$STORAGE_NODE($|\s)" | awk '{print $3}')" != "Completed" ]; do
            printf ".";
        done

        # Upgrade Runtime Node (POD)
        print_header "Upgrading Runtime Storage Node for - $NODE_NAME";
        kubectl set image deployment $STORAGE_NODE cortx-hax=$UPGRADE_IMAGE cortx-confd=$UPGRADE_IMAGE cortx-ios1=$UPGRADE_IMAGE cortx-ios2=$UPGRADE_IMAGE cortx-s31=$UPGRADE_IMAGE  cortx-s32=$UPGRADE_IMAGE cortx-s3auth=$UPGRADE_IMAGE  cortx-s3haproxy=$UPGRADE_IMAGE cortx-s3bgc=$UPGRADE_IMAGE;

        # Resume Runtime Storage Node (POD)
        print_header "Resuming Runtime Storage Node - Cluster";
        kubectl rollout resume deployment $STORAGE_NODE;
        sleep $TIMEDELAY;
    done
fi

# Pause Runtime Control Node (POD)
print_header "Pausing Runtime Control Node - Cluster";
kubectl rollout pause deployment control-node

# Create Upgrade Control Node (POD)
print_header "Creating Upgrade Control Node - Cluster";
kubectl apply -f "$BASEPATH/upgrade-pods/upgrade_control_node.yaml" --namespace "$NAMESPACE";

# Wait for Upgrade Control Node execution (POD)
printf "\nWaiting for Upgrade Control Node.";
while [ "$(kubectl get pods | grep -E "(^|\s)control-node($|\s)" | awk '{print $3}')" != "Completed" ]; do
    printf ".";
done
printf "\n";

# Upgrade Runtime Control Node (POD)
kubectl set image deployment control-node csm-agent=$UPGRADE_IMAGE s3-bg-producer=$UPGRADE_IMAGE

# Resume Runtime Control Node (POD)
print_header "Resuming Runtime Control Node - Cluster";
kubectl rollout resume deployment control-node
sleep $TIMEDELAY;

if [ $REDEFPODS = true ]; then
    # Pause Runtime HA Node (POD)
    print_header "Pausing Runtime Ha Node - Cluster";
    kubectl rollout pause deployment ha-node

    # Create Upgrade HA Node (POD)
    print_header "Creating Upgrade Ha Node - Cluster";
    kubectl apply -f "$BASEPATH/upgrade-pods/upgrade_ha_node.yaml" --namespace "$NAMESPACE";

    # Wait for Upgrade HA Node execution (POD)
    printf "\nWaiting for Upgrade Ha Node.";
    while [ "$(kubectl get pods | grep -E "(^|\s)ha-node($|\s)" | awk '{print $3}')" != "Completed" ]; do
        printf ".";
    done
    printf "\n";

    # Upgrade Runtime HA Node (POD)
    kubectl set image deployment ha-node cortx-ha=$UPGRADE_IMAGE 

    # Resume Runtime HA Node (POD)
    print_header "Resuming Runtime HA Node - Cluster";
    kubectl rollout resume deployment ha-node
    sleep $TIMEDELAY;
fi

# Delete Upgrade Storage/Data And Server RunTime Node (POD)
for NODE_INDEX in $(seq 1 $MAXNODES); do
    NODE_NAME="node$NODE_INDEX";
    if [ $REDEFPODS = true ]; then
        print_header "Deleting Upgrade Server and Data Nodes for - $NODE_NAME";
        kubectl delete pod server-$NODE_NAME --namespace "$NAMESPACE" ;
        kubectl delete pod data-$NODE_NAME --namespace "$NAMESPACE" ;
    else
        print_header "Deleting Upgrade Storage Node for - $NODE_NAME";
        kubectl delete pod storage-$NODE_NAME --namespace "$NAMESPACE" ;
    fi
    sleep $TIMEDELAY;
done

# Delete Upgrade Control Node (POD)
print_header "Deleting Upgrade Control Node - Cluster";
kubectl delete pod control-node --namespace "$NAMESPACE" &
sleep $TIMEDELAY;

if [ $REDEFPODS = true ]; then
    # Delete Upgrade HA Node (POD)
    print_header "Deleting Upgrade HA Node - Cluster";
    kubectl delete pod ha-node --namespace "$NAMESPACE" &
    sleep $TIMEDELAY
fi

# Wait for deletion of Upgrade nodes
wait;

# Ensure PID file is removed after upgrade is performed.
rm -f $UPGRADEPIDFILE
