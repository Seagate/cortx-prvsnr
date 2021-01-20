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
    provisioner pillar_set "cluster/${node}/bmc/ip" "\"$bmc_ip\""
else
    >&2 echo "BMC_IP is not configured"
    exit 1
fi
