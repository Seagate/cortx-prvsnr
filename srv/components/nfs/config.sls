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

{% set node = grains['id'] %}
{% set data_if = pillar['cluster'][node]['network']['data_nw']['iface'] %}

Create index:
  cmd.run:
    - name: m0libmotr -l {{ grains['ip4_interfaces'][data_if][0] }}@tcp:12345:44:301 -h {{ grains['ip4_interfaces'][data_if][0] }}@tcp:12345:45:1 -p '0x7000000000000001:1' -f '0x7200000000000000:0' index create "0x780000000000000b:1"

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
