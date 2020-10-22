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

{% for server, volume, mount_dir in salt['pillar.get']('glusterfs_mounts', []) %}

# TODO IMPROVE EOS-9581 there is a possible issue with fstab, SaltStack #39757

glusterfs_volume_{{ volume }}_mounted:
  mount.mounted:
    - name: {{ mount_dir }}
    - device: {{ server }}:{{ volume }}
    - mkmnt: True
    - fstype: glusterfs
    - opts: _netdev,defaults,acl
{%- if salt['grains.get']('virtual') != 'container' %}
    - persist: True
{%- else %}
    - persist: False
{%- endif %}
    - dump: 0
    - pass_num: 0

{% endfor %}
