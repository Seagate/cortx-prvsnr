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

{% if salt['service.status']('firewalld') %}

# Ensure ssh works when the firwall servcie starts for the next time
{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}
include:
  - .start
  - .stop

public:
  firewalld.present:
    - name: trusted
    - default: True
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False
    - require:
      - Start and enable firewalld service
    - watch_in:
      - Stop and disable Firewalld service

{% if ('data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0']) %}
Remove public data interfaces:
  cmd.run:
    - name: firewall-cmd --remove-interface=data0 --zone=public-data-zone --permanent
    - onlyif: firewall-cmd --get-zones | grep public-data-zone
    - require:
      - Start and enable firewalld service
    - watch_in:
      - Stop and disable Firewalld service
{% else %}
Remove public and private data interfaces:
  cmd.run:
    - names:
      - firewall-cmd --remove-interface={{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][0] }} --zone=public-data-zone --permanent
      - firewall-cmd --remove-interface={{ pillar['cluster'][grains['id']]['network']['data_nw']['iface'][1] }} --zone=trusted --permanent
    - onlyif: firewall-cmd --get-zones | grep public-data-zone
    - require:
      - Start and enable firewalld service
    - watch_in:
      - Stop and disable Firewalld service
{% endif %}

Remove public-data-zone:
  cmd.run:
    - name: firewall-cmd --permanent --delete-zone=public-data-zone
    - onlyif: firewall-cmd --get-zones | grep public-data-zone
    - require:
      - Start and enable firewalld service
      - public
    - watch_in:
      - Stop and disable Firewalld service

#{% if not ('data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0']) %}
# Remove private-data-zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --delete-zone=private-data-zone
#     - onlyif: firewall-cmd --get-zones | grep private-data-zone
#     - require:
#       - Start and enable firewalld service
#       - public
#     - watch_in:
#       - Stop and disable Firewalld service
#{% endif %}

# Remove management-zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --delete-zone=management-zone
#     - onlyif: firewall-cmd --get-zones | grep management-zone
#     - require:
#       - Start and enable firewalld service
#       - public
#     - watch_in:
#       - Stop and disable Firewalld service

{% endif %}

Delete firewall checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.firewall
