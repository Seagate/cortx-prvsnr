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

{% set node = grains['id'] %}

# Steps:
#  - unmount SWAP
#  - remove SWAP from fstab
#  - unmount /var/motr
#  - remove /var/motr partition
#  - delete SWAP and raw_metadata LVs
#  - delete vg_metadata_{{ node }}
#  - delete pv_metadata
#  - delete LVM partition
Unmount SWAP:
  cmd.run:
    - name: swapoff /dev/vg_metadata_{{ node }}/lv_main_swap || true

Remove swap from fstab:
  module.run:
    - mount.rm_fstab:
      - name: none
      - device: /dev/vg_metadata_{{ node }}/lv_main_swap
    - require:
      - Unmount SWAP

Remove LV swap:
  lvm.lv_absent:
    - name: lv_main_swap
    - vgname: vg_metadata_{{ node }}
    - require:
      - Remove swap from fstab

Remove LV raw_metadata:
  lvm.lv_absent: 
    - name: lv_raw_metadata
    - vgname: vg_metadata_{{ node }}

Remove VG:
  lvm.vg_absent:
    - name: vg_metadata_{{ node }}
    - require: 
      - Remove LV raw_metadata
      - Remove LV swap

Remove PV:
  lvm.pv_absent:
    - name: {{ pillar['cluster'][node]['storage']['metadata_devices'][0] }}2
    - require: 
      - Remove VG

Remove LVM partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_devices'][0] }}
      - minor: 2

Unmount /var/motr partition:
  mount.unmounted:
    - device: {{ pillar['cluster'][node]['storage']['metadata_devices'][0] }}1

Remove /var/motr partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_devices'][0] }}
      - minor: 1
# done with the sequence

Refresh partition:
  module.run:
    - partition.probe: 
      {% for device in pillar['cluster'][node]['storage']['metadata_devices'] %}
      - {{ device }}
      {% endfor %}
