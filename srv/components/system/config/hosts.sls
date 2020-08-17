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
