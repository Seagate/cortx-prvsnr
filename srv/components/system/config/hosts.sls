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

{% set server_nodes = [ ] -%}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
Hostsfile update for manangement interfaces:
  file.blockreplace:
    - name: /etc/hosts
    - backup: False
    - marker_start: "#---mgmt_nw_start---"
    - marker_end: "#---mgmt_nw_end---"
    - append_if_not_found: True
    - template: jinja
    - content: |
        {%- for node in server_nodes %}
        {%- for srvnode, ip_data in salt['mine.get'](node, 'node_ip_addrs') | dictsort() %}
        {% if ('mgmt0' in grains['ip4_interfaces']) and (grains['ip4_interfaces']['mgmt0'][0]) -%}
        {{ grains['ip4_interfaces']['mgmt0'][0] }}   {{ srvnode }}
        {% else -%}
        {{ ip_data[pillar['cluster'][srvnode]['network']['mgmt']['interfaces'][0]][0] }}   {{ srvnode }}
        {%- endif %}
        {% endfor -%}
        {%- endfor %}
        
Hostsfile update for data interfaces:
  file.blockreplace:
    - name: /etc/hosts
    - backup: False
    - marker_start: "#---data_nw_start---"
    - marker_end: "#---data_nw_end---"
    - append_if_not_found: True
    - template: jinja
    - content: |
        {%- for node in server_nodes %}
        {%- for srvnode, ip_data in salt['mine.get'](node, 'node_ip_addrs') | dictsort() %}
        {% if ('data0' in grains['ip4_interfaces']) and (grains['ip4_interfaces']['data0'][0]) -%}
        {{ grains['ip4_interfaces']['data0'][0] }}   {{ srvnode }}
        {% else -%}
        {{ ip_data[pillar['cluster'][srvnode]['network']['data']['public_interfaces'][0]][0] }}   {{ srvnode }}-data-public
        {{ ip_data[pillar['cluster'][srvnode]['network']['data']['private_interfaces'][0]][0] }}   {{ srvnode }}-data-private
        {% endif -%}
        {% endfor -%}
        {% endfor -%}
