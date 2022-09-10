#!/bin/bash -x
#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

source /etc/os-release

function add_primary_separator() {
    printf "\n################################################################################\n"
    printf "\t\t$*\n"
    printf "################################################################################\n"
}

function add_secondary_separator() {
    echo -e '\n==================== '"$*"' ====================\n'
}

function add_common_separator() {
    echo -e '\n--------------- '"$*"' ---------------\n'
}

function check_status() {
    return_code=$?
    error_message=$1
    if [ $return_code -ne 0 ]; then
            add_common_separator ERROR: "$error_message"
            exit 1
    fi
    add_common_separator SUCCESS
}

function validation() {
    if [ ! -f "$HOST_FILE" ]; then
        echo "$HOST_FILE is not present"
        exit 1
    fi

    if [ "$SOLUTION_CONFIG_TYPE" == "manual" ]; then
        if [ ! -f "$SOLUTION_CONFIG" ]; then
            echo "$SOLUTION_CONFIG is not present"
            exit 1
        fi
    fi
}

function k8s_deployment_type() {
    if [ "$(wc -l < "$HOST_FILE")" == "1" ]; then
        SINGLE_NODE_DEPLOYMENT="True"
        add_secondary_separator Single Node Deployment
    fi

    if [ "$(wc -l < "$HOST_FILE")" -ne "1" ]; then
        SINGLE_NODE_DEPLOYMENT="False"
        local UNTAINT_PRIMARY=$1
        if [ "$UNTAINT_PRIMARY" == "false" ]; then
            local NODES="$(wc -l < "$HOST_FILE")"
            local PRIMARY_NODE=1
            local NODES="$((NODES-PRIMARY_NODE))"
            add_secondary_separator $NODES node deployment
        else
            local NODES="$(wc -l < "$HOST_FILE")"
            add_secondary_separator "$NODES" node deployment
        fi
    fi
    if [ "$SINGLE_NODE_DEPLOYMENT" == "True"]; then
        echo "Setting up cluster for Single Node"
    fi
}

function scp_all_nodes() {
    for node in $ALL_NODES
        do 
            scp -q "$*" "$node":/var/tmp/
        done
}

function scp_primary_node() {
    for primary_nodes in $PRIMARY_NODE
        do
            scp -q "$*" "$primary_nodes":/var/tmp/
        done
}

function ssh_all_nodes() {
    for nodes in $ALL_NODES
        do
            ssh -o 'StrictHostKeyChecking=no' "$nodes" "$*"
        done
}

function ssh_primary_node() {
    ssh -o 'StrictHostKeyChecking=no' "$PRIMARY_NODE" "$*"
}

# Install yq 4.13.3

function install_yq() {
    YQ_VERSION=v4.13.3
    YQ_BINARY=yq_linux_386
    pip3 show yq && pip3 uninstall yq -y
    wget https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/${YQ_BINARY}.tar.gz -O - | tar xz && mv ${YQ_BINARY} /usr/bin/yq
    if [ -f /usr/local/bin/yq ]; then rm -rf /usr/local/bin/yq; fi    
    ln -s /usr/bin/yq /usr/local/bin/yq
}
