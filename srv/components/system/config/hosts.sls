#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

hostsfile:
  file.managed:
    - name: /etc/hosts
    - contents: |
        127.0.0.1     localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1           localhost localhost.localdomain localhost6 localhost6.localdomain6
        -------------------------------------------------------------------------------
        {%- for node in pillar['cluster']['node_list'] %}
        {%- if pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr'] %}
        {{ pillar['cluster'][node]['network']['data_nw']['pvt_ip_addr'] }}   {{ node -}}
        {%- else %}
        {%- for srvnode, ip_data in salt['mine.get'](node, 'node_ip_addrs') | dictsort() %}
        {{ ip_data[pillar['cluster'][srvnode]['network']['data_nw']['iface'][1]][0] }}   {{ srvnode -}}
        {% endfor -%}
        {% endif -%}
        {% endfor %}
    - user: root
    - group: root
