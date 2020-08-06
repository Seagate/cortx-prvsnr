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

# HA user has to be updated for setting new password.
# This has to happen only after pacemaker is installed.
Update ha user:
  user.present:
    - name: {{ pillar['corosync-pacemaker']['user'] }}
    - password: {{ salt['lyveutil.decrypt'](pillar['corosync-pacemaker']['secret'], 'corosync-pacemaker') }}
    - hash_password: True
    - createhome: False
    - shell: /sbin/nologin

#Configurations for Corosync and Pacemaker Setup
Add hacluster user to haclient group:
  group.present:
    - name: haclient
    - addusers:
      - {{ pillar['corosync-pacemaker']['user'] }}

Enable corosync service:
  service.dead:
    - name: corosync
    - enable: True

Enable pacemaker service:
  service.dead:
    - name: pacemaker
    - enable: True

Start pcsd service:
  service.running:
    - name: pcsd
    - enable: True

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Authorize nodes:
  pcs.auth:
    - name: pcs_auth__auth
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ node_id }}
      {%- endfor %}
    - pcsuser: {{ pillar['corosync-pacemaker']['user'] }}
    - pcspasswd: {{ salt['lyveutil.decrypt'](pillar['corosync-pacemaker']['secret'],'corosync-pacemaker') }}
    - extra_args:
      - '--force'
    - require:
      - Start pcsd service

Setup Cluster:
  pcs.cluster_setup:
    - nodes:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - {{ node_id }}
      {%- endfor %}
    - pcsclustername: {{ pillar['corosync-pacemaker']['cluster_name'] }}
    - extra_args:
      - '--start'
      - '--enable'
      - '--force'

Ignore the Quorum Policy:
  pcs.prop_has_value:
    - prop: no-quorum-policy
    - value: ignore

Enable STONITH:
  pcs.prop_has_value:
    - prop: stonith-enabled
{% if pillar['cluster'][grains['id']]['bmc']['ip'] %}
    - value: true
{% else %}
    - value: false
{% endif %}
{% else %}
No Cluster Setup:
  test.show_notification:
    - text: "Cluster setup applies only to primary node. There's no Cluster setup operation on secondary node"
{%- endif -%}
