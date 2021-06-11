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

{% for nw_interface in pillar['firewall'].keys() %}
  {% for service in pillar['firewall'][nw_interface]['ports'].keys() %}
    {% if service not in services %}

Update {{ service }} for {{ nw_interface }}:
  firewalld.service:
    - name: {{ service }}
    - ports:
      {% for port in pillar['firewall'][nw_interface]['ports'][service] %}
      - {{ port }}
      {% endfor %}

    {% do services.append(service) %}
    {% endif %}
  {% endfor %}
{% endfor %}

Add public data zone:
  module.run:
    - firewalld.new_zone:
      - public-data-zone
    - unless: firewall-cmd --list-all-zones | grep public-data-zone

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {% set data_if = ['data0'] %}
{% else %}
  {% set data_if = pillar['cluster'][grains['id']]['network']['data']['public_interfaces'] %}
{% endif %}

Public data zone:
  firewalld.present:
    - name: public-data-zone
    - default: False
    - prune_ports: True
    - prune_services: True
    - prune_interfaces: True
    - interfaces:
      {% for interface in data_if %}
      - {{ interface }}
      {% endfor %}
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

Add management zone:
  module.run:
    - firewalld.new_zone:
      - management-zone
    - unless: firewall-cmd --list-all-zones | grep management-zone

{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {% set mgmt_if = ['mgmt0'] %}
{% else %}
  {% set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt']['interfaces'] %}
{% endif %}
Management zone:
  firewalld.present:
    - name: management-zone
    - default: True
    - prune_ports: True
    - prune_services: True
    - prune_interfaces: True
    - interfaces:
    {% for interface in mgmt_if %}
      - {{ interface }}
    {% endfor %}
    - services:
      {% for service in pillar['firewall']['mgmt_public']['services'] %}
      - {{ service }}
      {% endfor %}
      {% for service in pillar['firewall']['mgmt_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}
    - require:
      - Add management zone
      {% for service in pillar['firewall']['mgmt_public']['ports'].keys() %}
      - {{ service }}
      {% endfor %}

Private data zone:
  firewalld.present:
    - name: trusted
    - default: False
    - masquerade: False
    - prune_ports: False
    - prune_services: False
    - prune_interfaces: True
    - interfaces:
      - lo
      {% for interface in pillar['cluster'][grains['id']]['network']['data']['private_interfaces'] %}
      - {{ interface }}
      {% endfor %}
    - sources:
      - 127.0.0.0/24
      {% if pillar['cluster'][grains['id']]['network']['data']['private_ip'] %}
      - {{ pillar['cluster'][grains['id']]['network']['data']['private_ip'].rsplit('.',1)[0] }}.0/24
      {% endif %}

Restart firewalld:
  module.run:
    - firewalld.reload_rules: []
    - service.restart:
      - firewalld
