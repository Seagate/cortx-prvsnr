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

{% for server, volume, mount_dir in salt['pillar.get']('glusterfs_mounts', []) %}

# TODO IMPROVE EOS-9581 there is a possible issue with fstab, SaltStack #39757

glusterfs_volume_{{ volume }}_mounted:
  mount.mounted:
    - name: {{ mount_dir }}
    - device: {{ server }}:{{ volume }}
    - mkmnt: True
    - fstype: glusterfs
    - opts: _netdev,defaults,acl
    - persist: True
    - dump: 0
    - pass_num: 0

{% endfor %}
