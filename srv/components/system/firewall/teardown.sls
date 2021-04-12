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

{% if salt['service.status']('firewalld') %}

# Ensure ssh works when the firwall servcie starts for the next time
{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}
include:
  - .start

public:
  firewalld.present:
    - name: trusted
    - default: True
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False
    - require:
      - Start and enable firewalld service

{% if ('data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0']) %}

Remove public data interfaces:
  cmd.run:
    - name: firewall-cmd --remove-interface=data0 --zone=public-data-zone --permanent
    - onlyif: firewall-cmd --get-zones | grep public-data-zone
    - require:
      - Start and enable firewalld service

{% else %}
Remove public and private data interfaces:
  cmd.run:
    - names:
      - firewall-cmd --remove-interface={{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] }} --zone=public-data-zone --permanent
      - firewall-cmd --remove-interface={{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] }} --zone=trusted --permanent
    - onlyif: firewall-cmd --get-zones | grep public-data-zone
    - require:
      - Start and enable firewalld service

{% endif %}

Remove public-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=public-data-zone
    - onlyif: firewall-cmd --get-zones | grep public-data-zone
    - require:
      - Start and enable firewalld service
      - public

Restart firewalld service post clean-up:
  module.run:
    - service.restart:
      - firewalld

{% endif %}

Delete firewall checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.firewall
