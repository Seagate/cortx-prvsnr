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

glusterfs_servers_peered:
  glusterfs.peered:
    - names:
{% for peer in salt['pillar.get']('glusterfs_peers', []) %}
      - {{ peer }}
{% endfor %}

# TODO IMPRVOVE ??? EOS-9581 it might be necessary
#      to add some sleep / wait here since 'peer probe' might be async ???

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
