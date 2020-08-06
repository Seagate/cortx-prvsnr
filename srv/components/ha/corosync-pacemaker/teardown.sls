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

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Destroy resource ClusterIP:
  cmd.run:
    - name: pcs resource delete ClusterIP
    - onlyif: pcs resource show ClusterIP

Remove authorized nodes:
  cmd.run:
    - names:
      {%- for node_id in pillar['cluster']['node_list'] %}
      - pcs cluster node remove {{ pillar['cluster'][node_id]['hostname'] }} --force || true
      {%- endfor %}

Destroy Cluster:
  cmd.run:
    - name: pcs cluster destroy --force || true
{% endif %}

Remove user and group:
  user.absent:
    - name: hacluster
    - purge: True
    - force: True

{% for serv in ["corosync", "pacemaker", "pcsd"] %}
Stop service {{ serv }}:
  service.dead:
    - name: {{ serv }}
    - enable: False
{% endfor %}

Remove pcs package:
  pkg.purged:
    - pkgs:
      - pcs
      - pacemaker
      - corosync
      - fence-agents-ipmilan

# Remove configuration directory:
#   file.absent:
#     - names:
#       - /etc/corosync
#       - /etc/pacemaker

Remove corosync-pacemaker data:
  file.absent:
    - names:
      - /var/lib/corosync
      - /var/lib/pacemaker
      - /var/lib/pcsd

# Enable and Start Firewall:
#   cmd.run:
#     - names:
#       - systemctl enable firewalld
#       - systemctl start firewalld
