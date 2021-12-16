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

function shutdown_pods(){
    while IFS= read -r line; do
        IFS=" " read -r -a deployments <<< "$line"
        kubectl scale deploy "${deployments[0]}" --replicas 0 --namespace=$namespace
    done <<< "$(kubectl get deployments --namespace=$namespace | grep $2)"

    printf "\nWait for $1 to be shutdown"
    while true; do
        output=$(kubectl get pods --namespace=$namespace | grep $3)
        if [[ "$output" == "" ]]; then
            break
        else
            printf "."
        fi
        sleep 1s
    done
}

function start_pods(){
    num_nodes=0
    while IFS= read -r line; do
        IFS=" " read -r -a deployments <<< "$line"
        kubectl scale deploy "${deployments[0]}" --replicas 1 --namespace=$namespace
        num_nodes=$((num_nodes+1))
    done <<< "$(kubectl get deployments --namespace=$namespace | grep $2)"

    printf "\nWait for $1 to be ready"
    while true; do
        count=0
        while IFS= read -r line; do
            IFS=" " read -r -a pod_status <<< "$line"
            IFS="/" read -r -a ready_status <<< "${pod_status[1]}"
            if [[ "${pod_status[2]}" != "Running" || "${ready_status[0]}" != "${ready_status[1]}" ]]; then
                break
            fi
            count=$((count+1))
        done <<< "$(kubectl get pods --namespace=$namespace | grep $3)"

        if [[ $num_nodes -eq $count ]]; then
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
done <<< "$(kubectl get pods --namespace=$namespace | grep 'control-node-.*\|storage-node.-.*')"


printf "########################################################\n"
printf "# Shutdown CORTX Control                                \n"
printf "########################################################\n"

shutdown_pods 'Control POD' 'control-node' 'control-node-.*'

printf "\n\n"
printf "CORTX Control pod has been shutdown"
printf "\n\n"


printf "########################################################\n"
printf "# Shutdown CORTX Storage                                   \n"
printf "########################################################\n"

shutdown_pods 'Storage POD' 'storage-node' 'storage-node.-.*'

printf "\n\n"
printf "All CORTX Storage pods have been shutdown"
printf "\n\n"

# Set new Image for All PODs
kubectl set image deployment control-node cortx-setup=$UPGRADE_IMAGE cortx-fsm-motr=$UPGRADE_IMAGE cortx-csm-agent=$UPGRADE_IMAGE cortx-bg-producer=$UPGRADE_IMAGE  cortx-message-server=$UPGRADE_IMAGE
for NODE_INDEX in $(seq 1 $MAXNODES); do
    STORAGE_NODE="storage-node$NODE_INDEX"
    kubectl set image deployment $STORAGE_NODE cortx-setup=$UPGRADE_IMAGE cortx-motr-hax=$UPGRADE_IMAGE cortx-motr-confd=$UPGRADE_IMAGE cortx-ios1=$UPGRADE_IMAGE cortx-ios2=$UPGRADE_IMAGE cortx-s31=$UPGRADE_IMAGE  cortx-s32=$UPGRADE_IMAGE cortx-s3-auth-server=$UPGRADE_IMAGE  cortx-s3-haproxy=$UPGRADE_IMAGE cortx-s3-bg-consumer=$UPGRADE_IMAGE;
done

printf "########################################################\n"
printf "# Start CORTX Control                                   \n"
printf "########################################################\n"

start_pods 'Control POD' 'control-node' 'control-node-.*'

printf "\n\n"
printf "All CORTX Control pods have been started"
printf "\n\n"

printf "########################################################\n"
printf "# Start CORTX Storage                                   \n"
printf "########################################################\n"

start_pods 'Storage POD' 'storage-node' 'storage-node.-.*'

printf "\n\n"
printf "All CORTX Storage pods have been started"
printf "\n\n"

# Ensure PID file is removed after upgrade is performed.
rm -f $UPGRADEPIDFILE
