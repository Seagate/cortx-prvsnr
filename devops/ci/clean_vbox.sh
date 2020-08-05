#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

#!/bin/bash

set -eu

mode="${1:-all}"

function usage {
  echo "\
Usage: $0 [{all|vms|dhcp|ifaces}] [--help]
"
}


function remove_vms {
    set -eux
    local _vm

    echo "Removing VirtualBox VMs ..."

    machines=$(vboxmanage list vms --long 2>/dev/null | grep "^Hardware UUID:" | awk '{print $3}')
    for _vm in $machines; do
        vboxmanage controlvm "$_vm" poweroff || true  # might fail if not running
        vboxmanage unregistervm --delete "$_vm"
    done
}


function remove_dhcpservers {
    set -eux
    local _server

    echo "Removing dhcp servers ..."
    
    dhcpservers=$(vboxmanage list dhcpservers 2>/dev/null | grep "^NetworkName:" | awk '{print $2}')
    for _server in $dhcpservers; do
        vboxmanage dhcpserver remove --netname "$_server"
    done
    echo "Done"
}


function remove_hostonlyifs {
    set -eux
    local _iface

    echo "Removing VirtualBox host-only networks ..."

    hostonlyifs=$(vboxmanage list hostonlyifs 2>/dev/null | grep "^Name:" | awk '{print $2}')
    for _iface in $hostonlyifs; do
        vboxmanage hostonlyif remove "$_iface"
    done
}


case "$mode" in
    -h|--help)
        usage
        exit 0
        ;;
    all)
        remove_vms
        remove_dhcpservers
        remove_hostonlyifs
        ;;
    vms)    remove_vms ;;
    dhcp)   remove_dhcpservers ;;
    ifaces) remove_hostonlyifs ;;
    *)
        >&2 echo "Unexpected mode '$mode'"
        usage
        exit 1
        ;;
esac
