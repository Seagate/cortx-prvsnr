#!/bin/bash
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

YQ_VERSION=v4.13.3
YQ_BINARY=yq_linux_386
SSH_KEY_FILE=/root/.ssh/id_rsa
HOST_FILE=$PWD/hosts
SCRIPT_PATH=/root/cortx-k8s/k8_cortx_cloud

function install_yq() {
    pip3 show yq && pip3 uninstall yq -y
    wget https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/${YQ_BINARY}.tar.gz -O - | tar xz && mv ${YQ_BINARY} /usr/bin/yq
    if [ -f /usr/local/bin/yq ]; then rm -rf /usr/local/bin/yq; fi
    ln -s /usr/bin/yq /usr/local/bin/yq
}

function update_solution_config() {
    pushd "$WORKSPACE"/devops/ci
        image=$CONTROL_IMAGE yq e -i '.solution.images.cortxcontrol = env(image)' solution_template.yaml
        image=$DATA_IMAGE yq e -i '.solution.images.cortxdata = env(image)' solution_template.yaml
        image=$SERVER_IMAGE yq e -i '.solution.images.cortxserver = env(image)' solution_template.yaml
        image=$HA_IMAGE yq e -i '.solution.images.cortxha = env(image)' solution_template.yaml
        image=$HA_IMAGE yq e -i '.solution.images.cortxclient = env(image)' solution_template.yaml
    popd
}

function generate_rsa_key() {
    if [ ! -f "$SSH_KEY_FILE" ]; then
        ssh-keygen -b 2048 -t rsa -f $SSH_KEY_FILE -q -N ""
     else
        echo $SSH_KEY_FILE already present
    fi
}

function check_status() {
    return_code=$?
    error_message=$1
    if [ $return_code -ne 0 ]; then
            echo "----------------------[ ERROR: $error_message ]--------------------------------------"
            exit 1
    fi
    echo "----------------------[ SUCCESS ]--------------------------------------"
}

function passwordless_ssh() {
    local NODE=$1
    local USER=$2
    local PASS=$3
    ping -c1 -W1 -q "$NODE"
    check_status
    yum install sshpass openssh-clients pdsh -y
    sshpass -p "$PASS" ssh-copy-id -f -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa.pub "$USER"@"$NODE"
    check_status "Passwordless ssh setup failed for $NODE. Please validate provided credentails"
}

function nodes_setup() {
    for ssh_node in $(cat "$HOST_FILE")
    do
        local NODE=$(echo "$ssh_node" | awk -F[,] '{print $1}' | cut -d'=' -f2)
        local USER=$(echo "$ssh_node" | awk -F[,] '{print $2}' | cut -d'=' -f2)
        local PASS=$(echo "$ssh_node" | awk -F[,] '{print $3}' | cut -d'=' -f2)

        echo "----------------------[ Setting up passwordless ssh for $NODE ]--------------------------------------"
        passwordless_ssh "$NODE" "$USER" "$PASS"
    done
}

function add_node_info_solution_config() {
    echo "Updating node info in solution.yaml"
    pushd "$WORKSPACE"/devops/ci
        if [ "$(wc -l < "$HOST_FILE")" == "1" ]; then
            local NODE=$(awk -F[,] '{print $1}' < "$HOST_FILE" | cut -d'=' -f2)
            i=$NODE yq e -i '.solution.nodes.node1.name = env(i)' solution_template.yaml
        else
            count=1
            for node in $(awk -F[,] '{print $1}' < "$HOST_FILE"| cut -d'=' -f2)
                do
                i=$node yq e -i '.solution.nodes.node'$count'.name = env(i)' solution_template.yaml
                count=$((count+1))
            done
            sed -i -e 's/- //g' -e '/null/d' solution_template.yaml
        popd
        fi
}

function copy_solution_file() {
    echo "Copying updated solution.yaml"
    pushd "$WORKSPACE"/devops/ci
        local ALL_NODES=$(awk -F[,] '{print $1}' < "$HOST_FILE"| cut -d'=' -f2)
        for node in $ALL_NODES
        do
            scp -q solution_template.yaml "$node":$SCRIPT_PATH/solution.yaml
        done
    popd
}

install_yq
generate_rsa_key
nodes_setup
update_solution_config
add_node_info_solution_config
copy_solution_file
