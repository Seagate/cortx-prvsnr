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

{#% set nwmanager_is_running = salt['service.status']('NetworkManager') %#}

{#% if nwmanager_is_running %#}

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
#     # - name: pkill -SIGTERM dhclient
#     - name: dhclient -x
#     - onlyif: pgrep dhclient
#     - requires:
#       - service: Stop and disable NetworkManager service

{#% if not pillar['cluster'][grains['id']]['network']['mgmt']['public_ip'] %#}
# Start dhclient:
#   cmd.run:
#     - name: dhclient -1 -q -H $(hostname -s) {{ pillar['cluster'][grains['id']]['network']['mgmt']['interfaces'][0] }}
#     - unless: pgrep dhclient
#     - onchanges:
#       - Kill dhclient
#
# Check_DNS:
#  cmd.script:
#    - source: salt://components/system/network/files/dns_check.sh
#    - require:
#      - Start dhclient
#    - retry:
#        attempts: 20
#        interval: 30
{#% endif %#}


{#% else  %#}

# network_manager_is_not_running:
#   test.nop: []

{#% endif %#}

Dummy placeholder for network.prepare:
  test.show_notification:
    - text: "A yaml file with comments results in minion non-zero exit"
