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

glusterfs_servers_peered:
  glusterfs.peered:
    - names:
{% for peer in salt['pillar.get']('glusterfs_peers', []) %}
      - {{ peer }}
{% endfor %}

# TODO IMPRVOVE ??? EOS-9581 it might be necessary
#      Added some sleep / wait here since 'peer probe' seems to be async

glusterfs_peers_wait:
  cmd.wait:
    - name: sleep 5
    - watch_in:
      - glusterfs_servers_peered

{% for volume, bricks in salt['pillar.get']('glusterfs_volumes', {}).items() %}

glusterfs_volume_{{ volume }}_created:
  glusterfs.volume_present:
    - name: {{ volume }}
    - bricks:
  {% for server, path in bricks.items() %}
      - {{ server }}:{{ path }}
  {% endfor %}
    - replica: {{ bricks|length }}
    - start: True
    - force: True
    - require:
      - glusterfs_servers_peered

{% endfor %}
