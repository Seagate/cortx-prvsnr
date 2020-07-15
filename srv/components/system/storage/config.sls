# Setup SWAP and /var/mero
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

{% if "physical" in grains['virtual'] %}
# Create single partition for LVM
Create LVM partition:
  module.run:
    - partition.mkpart:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext2
      - start: 0%
      - end: 100%
# done creating partitions

# Begin LVM config
# Set LVM flag on partition
# Convert metadata partion to LVM
Set LVM flag:
  module.run:
    - partition.toggle:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - 1
      - flag: lvm
      - require:
        - module: Create LVM partition
# done setting LVM flag

# Creating LVM physical volume using pvcreate
Make pv_metadata:
  module.run:
    - lvm.pvcreate:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    - require:
      - module: Set LVM flag
# done creating LVM physical volumes

# Creating LVM Volume Group (vg); vg_name = vg_metadata
Make vg_metadata:
  module.run:
    - lvm.vgcreate:
      - vgname: vg_metadata
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    - require:
      - module: Make pv_metadata
# done creating LVM VG

# Creating LVM's Logical Volumes (LVs; one for metadata, swap, and raw_metadata)
# Creating /var/motr metadata LV (size: 1TB)
Make lv_metadata:
  module.run:
    - lvm.lvcreate:
      - lvname: lv_metadata
      - vgname: vg_metadata
      - size: 1T
    - require:
      - module: Make vg_metadata

# Creating swap LV (size: 50% of total VG space)
Make lv_main_swap:
  module.run:
    - lvm.lvcreate:
      - lvname: lv_main_swap
      - vgname: vg_metadata
      - size: 50%VG
    - require:
      - module: Make vg_metadata

# Creating raw_metadata LV (per EOS-8858) (size: all remaining VG space; roughly 50% (less 1TB))
Make lv_raw_metadata:
  module.run:
    - lvm.lvcreate:
      - lvname: lv_raw_metadata
      - vgname: vg_metadata
      - size: 100%FREE
    - require:
      - module: Make vg_metadata
# done creating LVM LVs
# end LVM config

# Format SWAP and metadata (but not raw_metadata!)
# need to replace absolute path with proper structure
# Format SWAP
Make SWAP
  cmd.run:
    - name: sleep 10 && mkswap -f /dev/vg_metadata/lv_main_swap && sleep 5
    - onlyif: test -e /dev/vg_metadata/lv_main_swap
    - require:
      - module: Make lv_main_swap
      - cmd: Ensure SWAP partition is unmounted

# Activate SWAP device
Enable swap:
  mount.swap:
    - name: /dev/vg_metadata/lv_main_swap
    - persist: True    # don't add /etc/fstab entry
    - require:
      - cmd: Make SWAP

# Format 1TB metadata partition
Make metadata partition:
  module.run:
    - extfs.mkfs:
      - device: /dev/vg_metadata/lv_metadata
      - fstype: ext4
      - label: eos_metadata
      - require:
        - module: Make lv_metadata

# ---------------------------------- OLD stuff below ----------------------
# Format SWAP
#Make SWAP partition:
#  cmd.run:
#    - name: sleep 10 && mkswap -f {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2 && sleep 5
#    - onlyif: test -e {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
#    - require:
#      - module: Create swap partition
#      - cmd: Ensure SWAP partition is unmounted

# Activate SWAP device
#Enable swap:
#  mount.swap:
#    - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
#    - persist: True    # don't add /etc/fstab entry
#    - require:
#      - cmd: Make SWAP partition

# Format metadata partion
#Make raw_metadata partition:
#  module.run:
#    - extfs.mkfs:
#      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}3
#      - fs_type: ext4
#      - label: eos_raw_metadata
#      - require:
#        - module: Create raw_metadata partition
# ------------------------------------ end of OLD stuff --------------------

Refresh partition:
  cmd.run:
    - name: blockdev --flushbufs /dev/disk/by-id/dm-name-mpath* || true
  module.run:
    - partition.probe: []

{% else %}
# For VMs

# to-do: adjust VM config to use LVM

# Create partition for SWAP
Create swap partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: linux-swap
      - start: 0%
      - end: 50%

# Create partition for Metadata
Create metadata partition:
  module.run:
    - partition.mkpart:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext4
      - start: 50%
      - end: 100%

# Format SWAP
Make SWAP partition:
  cmd.run:
    - name: mkswap {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1 && sleep 5
    - onlyif: test -e {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    - require:
      - module: Create swap partition
      - cmd: Ensure SWAP partition is unmounted

# Activate SWAP device
Enable swap:
  mount.swap:
    - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    - persist: True    # don't add /etc/fstab entry
    - require:
      - cmd: Make SWAP partition

# Format metadata partion
Make metadata partition:
  module.run:
    - extfs.mkfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
      - fs_type: ext4
      - label: eos_metadata
      - require:
        - module: Create metadata partition

{% endif %}

# Refresh
{% if not 'single' in pillar['cluster']['type'] and pillar['cluster'][grains['id']]['is_primary'] -%}
Update partition tables of both nodes:
  cmd.run:
    - name: sleep 10; timeout -k 10 30 partprobe || true; ssh srvnode-2 "timeout -k 10 30 partprobe || true"

Update partition tables of primary node:
  cmd.run:
    - name: timeout -k 10 30 partprobe || true
{% endif %}
