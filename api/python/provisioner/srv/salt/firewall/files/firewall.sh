#!/bin/bash

set -eu

verbosity="${1:-0}"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi

#Disable iptables-services
systemctl stop iptables && systemctl disable iptables && systemctl mask iptables
#systemctl stop iptables6 && systemctl disable iptables6 && systemctl mask iptables6
systemctl stop ebtables && systemctl disable ebtables && systemctl mask ebtables

#Install and start firewalld
yum install -y firewalld
systemctl start firewalld
systemctl enable firewalld

# Open salt firewall ports
firewall-cmd --zone=public --add-port=4505-4506/tcp --permanent
firewall-cmd --reload
