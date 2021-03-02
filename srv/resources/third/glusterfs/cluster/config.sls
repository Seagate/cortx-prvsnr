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

{% set peers = salt['pillar.get']('glusterfs:peers') %}

glusterfs_servers_peered:
  glusterfs.peered:
    - names:
{% for peer in peers %}
      - {{ peer }}
{% endfor %}

{% for volume, export_dir in salt['pillar.get']('glusterfs:volumes').items() %}

gluster_brick_directory_{{ export_dir }}_exists:
  file.directory:
    - name: {{ export_dir }}
    - makedirs: true

glusterfs_volume_{{ volume }}_created:
  glusterfs.volume_present:
    - name: {{ volume }}
    - bricks:
    {% for peer in peers %}
      - {{ peer }}:{{ export_dir }}
    {% endfor %}
    - replica: {{ peers|length }}
    - start: True
    - force: True
    - require:
      - glusterfs_servers_peered
    #  Added retry here since 'peer probe' seems to be async
    - retry:
        attempts: 10
        until: True
        interval: 3

{% endfor %}
