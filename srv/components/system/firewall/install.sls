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

Install firewalld:
  pkg.installed:
    - name: firewalld

# Enable Firewalld
Unmask Firewall service:
  service.unmasked:
    - name: firewalld
    - require:
      - Install firewalld

# Ensure ssh works when the firwall servcie starts for the next time
{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] -%}
{%- endif -%}
Open public zone:
  firewalld.present:
    - name: public
    - default: True
    - ports:
      - 4505/tcp
      - 4506/tcp
    - prune_ports: False
    - services:
      - ssh
    - prune_services: False
    - prune_interfaces: False
    - require:
      - Ensure service running

Ensure service running:
  service.running:
    - name: firewalld
