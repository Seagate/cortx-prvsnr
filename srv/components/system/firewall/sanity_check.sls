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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}

# Verify NIC opened for management-zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --zone=management-zone --list-interfaces | grep {{ mgmt_if }}

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {%- set data_if = 'data0' -%}
{% else %}
  {%- set data_if = pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] -%}
{% endif %}
Verify NIC opened for public-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --zone=public-data-zone --list-interfaces | grep {{ data_if }}

{% if not ('data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0']) %}
Verify NIC opened for private-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --zone=trusted  --list-interfaces | grep {{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] }}
{% endif %}

Verify saltmaster ports:
  cmd.run:
    - name: firewall-cmd --permanent --service saltmaster --get-ports | grep -P '(?=.*?4505/tcp)(?=.*?4506/tcp)^.*$'

Verfiy csm ports:
  cmd.run:
    - name: firewall-cmd --permanent --service csm --get-ports | grep -P '(?=.*?8100/tcp)(?=.*?8101/tcp)(?=.*?8102/tcp)(?=.*8103/tcp)^.*$'

Verify consul ports:
  cmd.run:
    - name: firewall-cmd --permanent --service consul --get-ports | grep -P '(?=.*?8300/tcp)(?=.*?8301/tcp)(?=.*?8302/tcp)(?=.*?8301/udp)(?=.*?8302/udp)(?=.*?8500/tcp)(?=.*?8600/tcp)(?=.*?8600/udp)^.*$'

Verify hare ports:
  cmd.run:
    - name: firewall-cmd --permanent --service hare --get-ports | grep -P '(?=.*?8008/tcp)^.*$'

Verify lnet ports:
  cmd.run:
    - name: firewall-cmd --permanent --service lnet --get-ports | grep -P '(?=.*?988/tcp)^.*$'

Verify nfs ports:
  cmd.run:
    - name: firewall-cmd --permanent --service nfs --get-ports | grep -P '(?=.*?2049/tcp)(?=.*?2049/udp)(?=.*?32803/tcp)(?=.*?892/tcp)(?=.*?875/tcp)^.*$'

Verify openldap ports:
  cmd.run:
    - name: firewall-cmd --permanent --service openldap --get-ports | grep -P '(?=.*?389/tcp)^.*$'

# Verify s3 ports:
#   cmd.run:
#     - name: firewall-cmd --permanent --service s3 --get-ports | grep -P '(?=.*?7081/tcp)(?=.*?514/tcp)(?=.*?8125/tcp)(?=.*?6379/tcp)(?=.*?9080/tcp)(?=.*?9443/tcp)(?=.*?9086/tcp)(?=.*?80(8[1-9]))(?=.*?80(9[0-9]))^.*$'
