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

# Stop and disable NetworkManager service:
#   service.dead:
#     - name: NetworkManager
#     - enable: False

# Remove NetworkManager package:
#   pkg.purged:
#     - name: NetworkManager
#     - require:
#       - service: Stop and disable NetworkManager service

# Remove eth network interface configuration files:
#   cmd.run:
#     - name: rm -rf /etc/sysconfig/network-scripts/ifcfg-eth*
#     - onlyif: test -f /etc/sysconfig/network-scripts/ifcfg-eth0

# Remove lan0:
#   file.absent:
#     - name: /etc/sysconfig/network-scripts/ifcfg-lan0

# Disabling NetworkManager doesn't kill dhclient process.
# If not killed explicitly, it causes network restart to fail: COSTOR-439
# Kill dhclient:
#   cmd.run:
#     - name: pkill -SIGTERM dhclient
#     - onlyif: pgrep dhclient
#     - requires:
#       - service: Stop and disable NetworkManager service
