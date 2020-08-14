#!/bin/bash
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
    /usr/local/bin/provisioner pillar_set --targets "${node}" "cluster/${node}/bmc/ip" "\"$bmc_ip\""
else
    >&2 echo "BMC_IP is not configured"
    exit 1
fi
