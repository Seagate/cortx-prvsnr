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

{% if 'mgmt0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['mgmt0'] %}
  {% set mgmt_if = 'mgmt0' %}
{% else %}
  {% set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt']['interfaces'][0] %}
{% endif %}

Verify management zone interfaces:
  cmd.run:
    - name: firewall-cmd --zone=management-zone --list-interfaces | grep {{ mgmt_if }}

{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {% set public_data_if = ['data0'] %}
  {% set private_data_if = ['lo'] %}
{% else %}
  {% set public_data_if = pillar['cluster'][grains['id']]['network']['data']['public_interfaces'] %}
  {% set private_data_if = pillar['cluster'][grains['id']]['network']['data']['private_interfaces'] %}
{% endif %}

Verify public-data interfaces:
  cmd.run:
    - name: |
    {% for interface in public_data_if %}
        firewall-cmd --zone=public-data-zone --list-interfaces | grep {{ interface }}
    {% endfor %}

Verify private-data interfaces:
  cmd.run:
    - name: |
    {% for interface in private_data_if %}
        firewall-cmd --zone=trusted --list-interfaces | grep {{ interface }}
    {% endfor %}

{% for nic in pillar['firewall'].keys() %}

{% set zones =  ({'data_public':'public-data-zone','mgmt_public': 'management-zone'}) %}
{% set added_services = salt['firewalld.list_services'](zone=zones[nic]) %}
{% set services = pillar['firewall'][nic]['services'] %}
{% do services.extend(pillar['firewall'][nic]['ports'].keys() | list) %}

Verify {{ nic }} services:
{% if (added_services | symmetric_difference(services)) %}
  test.fail_without_changes:
    - name: "{{ (services | symmetric_difference(added_services)) }} services verification failed on {{ nic }} "
{% else %}
  test.show_notification:
    - text: {{ nic }} services verification successful
{% endif %}

{% set ports = [] %}
{% set added_ports = [] %}
{% do added_ports.extend(salt['firewalld.list_ports'](zone=zones[nic])) %}

{% for service in pillar['firewall'][nic]['ports'] %}

{% do added_ports.extend(salt['firewalld.get_service_ports'](service=service)) %}
{% do ports.extend(pillar['firewall'][nic]['ports'][service]) %}

{% endfor %}

Verify {{ nic }} ports:
{% if (added_ports | symmetric_difference(ports)) %}
  test.fail_without_changes:
    - name: "{{ (ports | symmetric_difference(added_ports)) }} ports verification failed on {{ nic }}"
{% else %}
  test.show_notification:
    - text: {{ nic }} ports verification successful
{% endif %}

{% endfor %}
