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
