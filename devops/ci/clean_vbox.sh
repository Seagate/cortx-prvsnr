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
