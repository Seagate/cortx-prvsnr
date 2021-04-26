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

# Setup SWAP and /var/motr
{% set node = grains['id'] %}

# Make SWAP
Ensure SWAP partition is unmounted:
  cmd.run:
    - name: swapoff -a && sleep 2

Label first LUN:
  module.run:
    - partition.mklabel:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - label_type: gpt

# Create /var/motr partition - it's NOT part of LVM!
Create metadata partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext4
      - start: 0%
{% if "physical" in grains['virtual'] %}
      - end: 1000GB
{% else %}
      - end: 10GB
{% endif %}

# Create single partition for LVM
Create LVM partition:
  module.run:
    - partition.mkpart:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext2
{% if "physical" in grains['virtual'] %}
      - start: 1001GB
{% else %}
      - start: 11GB
{% endif %}
      - end: 100%
# done creating partitions

# Begin LVM config
# Set LVM flag on partition
# Convert metadata partion to LVM
Set LVM flag:
  module.run:
    - partition.toggle:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - partition: 2
      - flag: lvm
    - require:
      - Create LVM partition
# done setting LVM flag

# Creating LVM physical volume using pvcreate
Make pv_metadata:
  lvm.pv_present:
    - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
    - require:
      - Set LVM flag
# done creating LVM physical volumes

# Creating LVM Volume Group (vg); vg_name = vg_metadata_{{ node }}
Make vg_metadata_{{ node }}:
  lvm.vg_present:
    - name: vg_metadata_{{ node }}
    - devices: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
    # - kwargs:
    #   - addtag: {{ node }}
    - require:
      - Make pv_metadata

# Since addtag is not supported yet in linux LVM Salt module
# Issue: https://github.com/saltstack/salt/issues/58747
# Proposed solution: https://github.com/saltstack/salt/pull/58748/files
# A workaround until the above issue is fixed
Add tag to vg_metadata_{{ node }}:
  cmd.run:
    - name: vgchange --addtag {{ node }} vg_metadata_{{ node }}

Refresh VG data:
  cmd.run:
    - name: vgscan --cache
    - require:
      - Add tag to vg_metadata_{{ node }}

# done creating LVM VG

# Creating LVM's Logical Volumes (LVs; one for swap and one for raw_metadata)
# Creating swap LV (size: 51% of total VG space - it must be larger than raw metadata)
Make lv_main_swap:
  lvm.lv_present:
    - name: lv_main_swap
    - vgname: vg_metadata_{{ node }}
    - extents: 51%VG          # Reference: https://linux.die.net/man/8/lvcreate
    - require:
      - Make vg_metadata_{{ node }}

# Creating raw_metadata LV (per EOS-8858) (size: all remaining VG space; roughly 49% (less 1TB))
Make lv_raw_metadata:
  lvm.lv_present:
    - name: lv_raw_metadata
    - vgname: vg_metadata_{{ node }}
    - extents: 100%FREE        # Reference: https://linux.die.net/man/8/lvcreate
    - require:
      - Make vg_metadata_{{ node }}
# done creating LVM LVs
# end LVM config

# Format SWAP and metadata (but not raw_metadata!)
# need to replace absolute path with proper structure
# Format SWAP
Make SWAP:
  cmd.run:
    - name: sleep 10 && mkswap -f /dev/vg_metadata_{{ node }}/lv_main_swap && sleep 5
    - onlyif: test -e /dev/vg_metadata_{{ node }}/lv_main_swap
    - require:
      - Make lv_main_swap
      - cmd: Ensure SWAP partition is unmounted

Verify sysvol_swap parition in the fstab:
  module.run:
    - mount.set_fstab:
      - name: swap
      - device: /dev/mapper/vg_sysvol-lv_swap
      - fstype: swap
      - opts:
        - defaults
        - pri=0

Verify lv_main_swap parition in the fstab:
  module.run:
    - mount.set_fstab:
      - name: none
      - device: /dev/vg_metadata_{{ node }}/lv_main_swap
      - fstype: swap
      - opts:
        - defaults
        - pri=32767
      - require:
        - cmd: Make SWAP

Enable sysvol_swap:
  module.run:
    - mount.swapon:
      - name: /dev/mapper/vg_sysvol-lv_swap
      - priority: "0"

Enable lv_main_swap:
  module.run:
    - mount.swapon:
      - name: /dev/vg_metadata_{{ node }}/lv_main_swap
      - priority: 32767

# Format metadata partion
Make metadata partition:
  module.run:
    - extfs.mkfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
      - fs_type: ext4
      - label: cortx_metadata
      - require:
        - Create metadata partition

# ---------------------------------- OLD stuff below ----------------------
# Format SWAP
#Make SWAP partition:
#  cmd.run:
#    - name: sleep 10 && mkswap -f {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2 && sleep 5
#    - onlyif: test -e {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
#    - require:
#      - Create swap partition
#      - cmd: Ensure SWAP partition is unmounted

# Activate SWAP device
#Enable swap:
#  mount.swap:
#    - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
#    - persist: True    # don't add /etc/fstab entry
#    - require:
#      - cmd: Make SWAP partition
# ------------------------------------ end of OLD stuff --------------------

Refresh partition:
  cmd.run:
    - name: blockdev --flushbufs /dev/disk/by-id/dm-name-mpath* || true
  module.run:
    - partition.probe: []

# Refresh
{% if (1 < pillar['cluster']['node_list'] | length) and (pillar['cluster'][grains['id']]['is_primary']) -%}
Update partition tables of both nodes:
  cmd.run:
    - name: sleep 10; timeout -k 10 30 partprobe || true; ssh srvnode-2 "timeout -k 10 30 partprobe || true"

Update partition tables of primary node:
  cmd.run:
    - name: timeout -k 10 30 partprobe || true
{% endif %}
