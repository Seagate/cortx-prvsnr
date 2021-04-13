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
  {% set mgmt_if = ['mgmt0'] %}
{% else %}
  {% set mgmt_if = pillar['cluster'][grains['id']]['network']['mgmt']['interfaces'] %}
{% endif %}

{% set added_mgmt_if = salt['firewalld.get_interfaces'](zone='management-zone') %}
Verify management zone interfaces:
{% if (added_mgmt_if | symmetric_difference(mgmt_if)) %}
  test.fail_without_changes:
    - name: {{ (added_mgmt_if | symmetric_difference(mgmt_if)) }} interface verification failed on management-zone
{% else %}
  test.show_notification:
    - text: Interfaces verification successful on management-zone
{% endif %}


{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] %}
  {% set public_data_if = ['data0'] %}
  {% set private_data_if = ['lo'] %}
{% else %}
  {% set public_data_if = pillar['cluster'][grains['id']]['network']['data']['public_interfaces'] %}
  {% set private_data_if = pillar['cluster'][grains['id']]['network']['data']['private_interfaces'] %}
  {% do private_data_if.extend(['lo']) %}
{% endif %}

{% set added_public_data_if = salt['firewalld.get_interfaces'](zone='public-data-zone') %}
Verify public data interfaces:
{% if (added_public_data_if | symmetric_difference(public_data_if)) %}
  test.fail_without_changes:
    - name: {{ (added_public_data_if | symmetric_difference(public_data_if)) }} interface verification failed on public-data-zone
{% else %}
  test.show_notification:
    - text: Interfaces verification successful on public-data-zone
{% endif %}

{% set added_private_data_if = salt['firewalld.get_interfaces'](zone='trusted') %}
Verify private data interfaces:
{% if (added_private_data_if | symmetric_difference(private_data_if)) %}
  test.fail_without_changes:
    - name: {{ (added_private_data_if | symmetric_difference(private_data_if)) }} interface verification failed on private-data-zone
{% else %}
  test.show_notification:
    - text: Interfaces verification successful on private-data-zone
{% endif %}

{% for network_interface in pillar['firewall'].keys() %}

{% set zones =  ({'data_public':'public-data-zone','mgmt_public': 'management-zone'}) %}
{% set added_services = salt['firewalld.list_services'](zone=zones[network_interface]) %}
{% set services = pillar['firewall'][network_interface]['ports'].keys() | list %}

{% if pillar['firewall'][network_interface]['services'] %}
{% do services.extend(pillar['firewall'][network_interface]['services']) %}
{% endif %}

Verify {{ network_interface }} services:
{% if (added_services | symmetric_difference(services)) %}
  test.fail_without_changes:
    - name: {{ (services | symmetric_difference(added_services)) }} services verification failed on {{ network_interface }}
{% else %}
  test.show_notification:
    - text: {{ network_interface }} services verification successful
{% endif %}

{% set ports = [] %}
{% set added_ports = [] %}
{% do added_ports.extend(salt['firewalld.list_ports'](zone=zones[network_interface])) %}

{% for service in pillar['firewall'][network_interface]['ports'] %}

{% do added_ports.extend(salt['firewalld.get_service_ports'](service=service)) %}
{% do ports.extend(pillar['firewall'][network_interface]['ports'][service]) %}

{% endfor %}

Verify {{ network_interface }} ports:
{% if (added_ports | symmetric_difference(ports)) %}
  test.fail_without_changes:
    - name: "{{ (ports | symmetric_difference(added_ports)) }} ports verification failed on {{ network_interface }}"
{% else %}
  test.show_notification:
    - text: {{ network_interface }} ports verification successful
{% endif %}

{% endfor %}

Validate pillar firewall:
  module.run:
    - lyveutils.validate_firewall: []

