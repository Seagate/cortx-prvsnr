# HOW TO SYNC:
# - salt "<node which is to be sync>" state.apply components.sync.files.config <specify components as {'component': ['hare']}>
# - Example - If updated data is in node-1 and need to sync other nodes[node-2 and node-3] with node-1 data
# - then run - salt -L "srvnode-2,srvnode-3" state.apply components.sync.files.config {'component':['hare']}
# - If updated data is in node-2 and need to sync other nodes[node-1 and node-3] with node-2 data then 
# - then run - salt -L "srvnode-1,srvnode-3" state.apply components.sync.files.config {'component':['hare','csm']}


{%- set components = salt['pillar.get']('components', ['hare','csm']) %}
{%- if 'srvnode-1' in grains['id'] %}
{%- set node = 'srvnode-2' %}
{%- else %}
{%- set node = 'srvnode-1' %}
{%- endif %}
Sync Files across nodes:
  cmd.run:
    name: |
      {%- for component in components %}
      {%- set yaml_file = '/opt/seagate/cortx/{0}/conf/setup.yaml'.format(component) %}
      {%- import_yaml yaml_file as yaml %}
      {%- for file_name in yaml[component]["backup"]["files"] %}
      rsync -zavhe ssh {{ node }}:{{ file_name }} {{ file_name }}
      {%- endfor %}
      {%- endfor %}
