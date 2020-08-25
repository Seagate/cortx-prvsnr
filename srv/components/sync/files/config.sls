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


# HOW TO SYNC:
# - salt "<node which is to be sync>" state.apply components.sync.files.config <specify components as {'component': ['hare']}>
# - Example - If updated data is in node-1 and need to sync other nodes[node-2 and node-3] with node-1 data
# - then run - salt -L "srvnode-2,srvnode-3" state.apply components.sync.files.config {'component':['hare']}
# - If updated data is in node-2 and need to sync other nodes[node-1 and node-3] with node-2 data then 
# - then run - salt -L "srvnode-1,srvnode-3" state.apply components.sync.files.config {'component':['hare','csm']}


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
