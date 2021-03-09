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

{% for volume in salt['pillar.get']('glusterfs:volumes', []) %}

# unmount gluster volume
glusterfs_volume_dir_{{ volume['mount_dir'] }}_unmount:
  mount.unmounted:
    - name: {{ volume['mount_dir'] }}
    - persist: True

# remove mount dir from fstab
Remove mount_{{ volume['mount_dir'] }}_present_in_fstab:
  file.line:
    - name: '/etc/fstab'
    - mode: delete
    - match: {{ volume['mount_dir'] }}

{% if "primary" in pillar["cluster"][grains["id"]]["roles"] %}

# remove gluster volume
glusterfs_volume_{{ volume['name'] }}_removed:
  module.run:
    - name: glusterfs.delete_volume
    - target: {{ volume['name'] }}

{% endif %}

# remove mount dir
# Remove gluster_{{ volume['mount_dir'] }}_mount_dir:
#  file.absent:
#    - name: {{ volume['mount_dir'] }}
#    - require:
#      - glusterfs_volume_dir_{{ volume['mount_dir'] }}_unmount

# remove brick dir
# Remove gluster_{{ volume['export_dir'] }}_brick_dir:
# file.absent:
#    - name: {{ volume['export_dir'] }}

{% endfor %}
