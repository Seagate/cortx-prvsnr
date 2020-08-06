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

{% set node = grains['id'] %}
{% set data_if = pillar['cluster'][node]['network']['data_nw']['iface'] %}

Create index:
  cmd.run:
    - name: m0clovis -l {{ grains['ip4_interfaces'][data_if][0] }}@tcp:12345:44:301 -h {{ grains['ip4_interfaces'][data_if][0] }}@tcp:12345:45:1 -p '0x7000000000000001:1' -f '0x7200000000000000:0' index create "0x780000000000000b:1"

Initialize KVSNS:
  cmd.run:
    - name: kvsns_init

Start NFS Server:
  cmd.run:
    - name: ganesha.nfsd -L /dev/tty -F -f /etc/ganesha/ganesha.conf

Mount NFS4:
  mount.mounted:
    - name: /mnt/nfs_mount
    - device: {{ grains['ip4_interfaces'][data_if][0] }}:/kvsns
    - fstype: nfs4
    - mkmnt: True
