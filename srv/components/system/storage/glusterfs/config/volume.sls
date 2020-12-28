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

{% set nodes = salt['pillar.get']('cluster:node_list', []) %}

{% for volume in salt['pillar.get']('glusterfs:volumes', []) %}

{% for node in nodes %}

glusterfs_add_brick_to_{{ volume['name'] }}_volume_on_{{ node }}:
  module.run:
    - gluster.add_brick:
      - volume: {{ volume['name'] }}
      - brick: {{ salt['pillar.get']('cluster:'+node+':hostname') }}:{{ volume['export_dir'] }}

{% endfor %}

{% endfor %}
