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

include:
  - .start

{% set services = [] %}

{% for nic in pillar['firewall'].keys() %}

{% for service in pillar['firewall'][nic]['ports'] %}

{% if service not in services %}

{{ service }}:
  firewalld.service:
    - name: {{ service }}
    - ports:
      {% for port in pillar['firewall'][nic]['ports'][service] %}
      - {{ port }}
      {% endfor %}



{% do services.append(service) %}
{% endif %}


{% endfor %}

{% endfor %}



Add public data zone:
  cmd.run:
    - name: firewall-cmd --permanent --new-zone public-data-zone
    - unless: firewall-cmd --get-zones | grep public-data-zone
    - watch_in:
      - Start and enable firewalld service

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] -%}
Data-zone:
  firewalld.present:
    - name: public-data-zone
    - interfaces:
      - data0
    - default: False
    - prune_ports: True
    - prune_services: True
    - prune_interfaces: True
    - services:
      {% for service in pillar['firewall']['data_public']['services'] %}
      - {{ service }}
      {% endfor %}
      {% for service in pillar['firewall']['data_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}
    - require:
      - Add public data zone
      {% for service in pillar['firewall']['data_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}

# No restrictions for localhost
Localhost:
  firewalld.present:
    - name: trusted
    - interfaces:
      - lo
    - sources:
      - 127.0.0.0/24
    - default: False
    - masquerade: False
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False

{% else -%}
Public data zone:
  firewalld.present:
    - name: public-data-zone
    - default: False
    - prune_ports: True
    - prune_services: True
    - prune_interfaces: True
    - services:
      {% for service in pillar['firewall']['data_public']['services'] %}
      - {{ service }}
      {% endfor %}
      {% for service in pillar['firewall']['data_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}
    - interfaces:
      {% for interface in pillar['cluster'][grains['id']]['network']['data']['public_interfaces'] %}
      - {{ interface }}
      {% endfor %}
    # - rich_rules:
    #   - 'rule family="ipv4" destination address="224.0.0.18" protocol value="vrrp" accept'
    - require:
      - Add public data zone
      {% for service in pillar['firewall']['data_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}

Private data zone:
  firewalld.present:
    - name: trusted
    - interfaces:
      {% for interface in pillar['cluster'][grains['id']]['network']['data']['private_interfaces'] %}
      - {{ interface }}
      {% endfor %}
    - default: False
    - sources:
      - 127.0.0.0/24
      - 192.168.0.0/16
    - masquerade: False
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: False
{%- endif %}

{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {%- set mgmt_if = 'mgmt0' -%}
{% else %}
  {%- set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt']['interfaces'][0] -%}
{% endif %}
# Add management zone:
#   cmd.run:
#     - name: firewall-cmd --permanent --new-zone management-zone
#     - unless: firewall-cmd --get-zones | grep management-zone
#     - watch_in:
#       - Start and enable firewalld service

Management zone:
  firewalld.present:
    - name: public
    - default: True
    - prune_ports: True
    - prune_services: True
    - services:
      {% for service in pillar['firewall']['mgmt_public']['services'] %}
      - {{ service }}
      {% endfor %}
      {% for service in pillar['firewall']['mgmt_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}
      {% if salt['cmd.run']('rpm -qa glusterfs-server') %}
      - glusterfs
      {% endif %}
    - interfaces:
      - {{ mgmt_if }}
    - port_fwd:
      {% if "primary" in pillar["cluster"][grains["id"]]["roles"] %}
      - {{ pillar['storage']['enclosure-1']['controller']['primary']['port'] }}:80:tcp:{{ pillar['storage']['enclosure-1']['controller']['primary']['ip'] }}
      {% else %}
      - {{ pillar['storage']['enclosure-1']['controller']['primary']['port'] }}:80:tcp:{{ pillar['storage']['enclosure-1']['controller']['secondary']['ip'] }}
      {% endif %}
    - require:
      # - Add management zone
      {% for service in pillar['firewall']['mgmt_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}

# Public Zone:
#   firewalld.present:
#     - name: public
#     - block_icmp:
#       - echo-reply
#       - echo-request
#     - masquerade: True
#     - prune_services: False
#     - prune_ports: True
#     - prune_interfaces: True
#     - require:
#       - Public data zone
#       - Management zone
#     - watch_in:
#       - service: Start and enable firewalld service

Restart firewalld:
  module.run:
    - cmd.run:
      - firewall-cmd --reload
    # - service.restart:
    #   - firewalld
