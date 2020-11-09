#!/bin/sh
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#


set -eu

export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/utils.log}"


function _lerror {
    local msg=${1}
    echo -e "[ERROR  $(date +'%Y-%m-%d %H:%M:%S')] ${msg}" 2>&1 | tee -a ${LOG_FILE}
}

function _linfo {
    local msg=${1}
    echo -e "${msg}" 2>&1 | tee -a ${LOG_FILE}
    echo -e "[INFO  $(date +'%Y-%m-%d %H:%M:%S')] ${msg}" >> ${LOG_FILE}  2>&1
}

function get_pillar_data {
    local l_key=${1:-}

    if [[ $# -gt 1 ]]; then
        _lerror "$0: Only one positional argument is expected, provided: $@"
        exit 2
    elif [[ $# -eq 0 ]]; then
        _lerror "$0: This function expects an argument."
        exit 1
    fi

    local l_val=$(salt-call --local pillar.get "${l_key}" --output=newline_values_only)
    echo ${l_val}
}


# Remote execute a command over private data interface
function remote_execute {
    remote_node=${1:-192.168.0.2}
    cmd=${2:-}

    if [[ -n ${cmd} ]]; then
        echo $(ssh -o "StrictHostKeyChecking=no" -i /root/.ssh/id_rsa_prvsnr "${remote_node}" "${cmd}")
        return $?
    else
        _lerror "$0: The method for remote execution is called without passing the intended command."
        return 20
    fi
}


# Check if user wants to proceed
function proceed_check {
    while true; do
        read -n1 -p "Do you wish to proceed? (y/n): " _ans
        case $_ans in
            [Yy]* ) break;;
            [Nn]* ) exit 10;;
            * ) echo "Please answer y or n.";;
        esac
    done
}


function ensure_healthy_cluster {
    local _nowait=${1:-}

    _linfo "*****************************************************************"
    _linfo "Performing HA cluster health-check."
    _linfo "*****************************************************************"

    _linfo "Checking nodes online."

    attempt=0
    while /usr/bin/true; do
        hctl node status --full > /tmp/hctl_cluster_health.json

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

                    if [[ "$_nowait" == true ]]; then
                        answer='y'
                    elif [[ "$_nowait" == false ]]; then
                        answer='n'
                    else
                        echo -n "Proceed ('y' to proceed/'n' to wait)? " 2>&1 | tee -a ${LOG_FILE}
                        read answer
                    fi

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
