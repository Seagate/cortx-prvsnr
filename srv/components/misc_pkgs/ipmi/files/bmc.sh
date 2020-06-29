#!/bin/bash

# TODO TEST EOS-8473

set -eu

node="${1:-srvnode-1}"
verbosity="${2:-0}"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi

bmc_ip_line=$(ipmitool lan print 1|grep -oP 'IP Address.+:.*\d+')
bmc_ip=$(echo ${bmc_ip_line}|cut -f2 -d':'|tr -d ' ')

if [[ -n "$bmc_ip" && "$bmc_ip" != "0.0.0.0" ]]; then
    echo "BMC_IP detected as $bmc_ip"
    provisioner pillar_set --targets "${node}" "cluster/${node}/bmc/ip" "\"$bmc_ip\""
else
    >&2 echo "BMC_IP is not configured"
    exit 1
fi
