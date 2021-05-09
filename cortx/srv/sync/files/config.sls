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

# HOW TO SYNC:
# - salt "<node which is to be sync>" state.apply sync.files.config <specify components as {'component': ['hare']}>
# - Example - If updated data is in node-1 and need to sync other nodes[node-2 and node-3] with node-1 data
# - then run - salt -L "srvnode-2,srvnode-3" state.apply sync.files.config {'component':['hare']}
# - If updated data is in node-2 and need to sync other nodes[node-1 and node-3] with node-2 data then 
# - then run - salt -L "srvnode-1,srvnode-3" state.apply sync.files.config {'component':['hare','csm']}


{% set components = ['iostack-ha', 'csm'] %}
{% if 'srvnode-1' in grains['id'] %}
{% set node = 'srvnode-2' %}
{% else %}
{% set node = 'srvnode-1' %}
{% endif %}
{% for component in components %}
{% set yaml_file = '/opt/seagate/cortx/{0}/conf/setup.yaml'.format(component) %}
{% import_yaml yaml_file as yaml_str %}
{% if yaml_str[component]["backup"] and yaml_str[component]["backup"]["files"] %}
{% for file_name in yaml_str[component]["backup"]["files"] %}
Sync file {{ file_name }} across nodes:
  cmd.run:
    - name: rsync -zavhe ssh {{ node }}:{{ file_name }} {{ file_name }}
{% endfor %}
{% endif %}
{% endfor %}
