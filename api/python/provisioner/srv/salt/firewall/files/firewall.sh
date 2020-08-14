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
