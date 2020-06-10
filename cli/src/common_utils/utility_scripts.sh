#!/bin/sh

set -eu

export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/utils.log}"
truncate -s 0 ${LOG_FILE}

function get_pillar_data {
    local l_key=${1:-}

    if [[ $# -gt 1 ]]; then
        echo "[ERROR] $0: Only one positional argument is expected, provided: $@" | tee -a ${LOG_FILE}
        exit 2
    elif [[ $# -eq 0 ]]; then
        echo "[ERROR] $0: This function expects an argument." | tee -a ${LOG_FILE}
        exit 1
    fi

    local l_val=$(salt-call pillar.get ${l_key} --output=newline_values_only)
    echo ${l_val}
}

function ensure_healthy_cluster {
    _linfo "*****************************************************************"
    _linfo "Performing HA cluster health-check."
    _linfo "*****************************************************************"
    hctl node status --full > /tmp/hctl_cluster_health.json

    _linfo "Checking nodes online."

    attempt=0
    while /usr/bin/true; do
        if [[ ("true" == "$(jq '.nodes[]|select(.name=="srvnode-1").online' /tmp/hctl_cluster_health.json)") && ("true" == "$(jq '.nodes[]|select(.name=="srvnode-2").online' /tmp/hctl_cluster_health.json)") ]]; then
            # Cluster is Online, we are part happy but would continue further with checks
            _linfo " Cluster is Online, we are part happy.  "
            _linfo " But, would continue further with few more checks. "

            configured=$(pcs cluster status | grep "resources configured" | xargs | cut -d ' ' -f1)
            disabled=$(pcs cluster status | grep "resources configured" | xargs | cut -d ' ' -f4 | cut -d '(' -f2)
            running_node1=$(jq .nodes[0].resources_running /tmp/hctl_cluster_health.json)
            running_node2=$(jq .nodes[1].resources_running /tmp/hctl_cluster_health.json)
            # running=$(jq .resources.statistics.started /tmp/hctl_cluster_health.json)
            running=$(( running_node1 + running_node2 ))
            stopped=$(jq .resources.statistics.stopped /tmp/hctl_cluster_health.json)

            configured=${configured:-0}
            disabled=${disabled:-0}
            running=${running:-0}
            stopped=${stopped:-0}

            if [[ "${running}" == "$(( configured - disabled ))" ]]; then
                if [[ "0" == "${stopped}" ]]; then
                    _linfo " Cluster is Online and all services have started. "
                    
                    # Break the loop
                    break
                else
                    _linfo " Cluster is Online, we are part happy as it seems few services are disabled. "

                    echo -n "Proceed ('y' to proceed/'n' to wait)? " 2>&1 | tee -a ${LOG_FILE}
                    read answer

                    if [ "$answer" != "${answer#[Yy]}" ] ;then
                        _linfo "User has decided to proceed with the current HA status."
                        # Break the loop and proceed
                        break
                    else
                        _linfo "User has decided to proceed with wait. Re-attempting in 10 secs."{LOG_FILE}
                        sleep 10
                    fi
                fi
            else
                _linfo "Something's not right. All resources are not started..."

                if [[ ${attempt} -ge 10 ]]; then
                    _lerror "Giving up after ${attempt} attempts."
                    exit 20
                fi
            fi

        else
            _lerror "One or more nodes in cluster is/are Offline. Attempt: ${attempt}"
            
            # Try 10 attempts and give-up
            if [[ ${attempt} -ge 10 ]]; then
                _lerror "One or more nodes in cluster is/are Offline."
                _lerror "Giving up after 10 attempts."
                exit 10
            fi
        fi

        # Increment attempt count
        attempt=$(( attempt+1 ))
        sleep 10
    done

    _linfo "*****************************************************************"
}
