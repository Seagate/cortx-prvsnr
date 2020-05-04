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
# For HW
# Preserve space for OS RAID/LVM partitions
# /boot/efi  (note: this is partition #1)
Create EFI partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: fat32
      - start: 0%
      - end: 256MB

# /boot  (note: this is partition #2)
Create boot partition:
  module.run:
    - partition.mkpart:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext2
      - start: 256MB
      - end: 1GB

# The rest of the OS partitions (except /var/crash) (note: this is partition #3)
Create OS partition:
  module.run:
    - partition.mkpart:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext2
      - start: 1GB
      - end: 5%

# /var/crash (not under RAID or LVM control; size ~1TB; note: this is partition #4)
Create var_crash partition:
  module.run:
    - partition.mkpart:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext2
      - start: 6%
      - end: 10%
# done with the OS partitions

# Create partition for SWAP (note: this is partition #5)
Create swap partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: linux-swap
      - start: 11%
      - end: 50%

# Create partition for Metadata (note: this is partition #6)
Create metadata partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext4
      - start: 51%
      - end: 100%

# Begin partitioning
# Create /boot/efi
Make EFI partition:
  cmd.run:
    - name: mkfs -t vfat {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    - require:
      - module: Create EFI partition

# Create /boot RAID (set flag)
Make boot RAID:
  module.run:
    - partition.toggle:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - 2
      - flag: raid
    - require:
      - module: Create boot partition

# Create / RAID (set flag)
Make ROOT RAID:
  module.run:
    - partition.toggle:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - 3
      - flag: raid
    - require:
      - module: Create OS partition

# Create /var/crash
Make var_crash partition:
  module.run:
    - extfs.mkfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}4
      - fs_type: ext4
      - label: varcrash
      - require:
        - module: Create var_crash partition

# Format SWAP
Make SWAP partition:
  cmd.run:
    - name: mkswap -f {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}5 && sleep 5
    - onlyif: test -e {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}5
    - require:
      - module: Create swap partition
      - cmd: Ensure SWAP partition is unmounted

# Activate SWAP device
Enable swap:
  mount.swap:
    - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}5
    - persist: True    # don't add /etc/fstab entry
    - require:
      - cmd: Make SWAP partition

# Format metadata partion
Make metadata partition:
  module.run:
    - extfs.mkfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}6
      - fs_type: ext4
      - label: eos_metadata
      - require:
        - module: Create metadata partition
{% else %}
# For VMs
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

Refresh partition:
  cmd.run:
    - name: blockdev --flushbufs /dev/disk/by-id/dm-name-mpath* || true
  module.run:
    - partition.probe: []

# Refresh
{% if pillar['cluster'][grains['id']]['is_primary'] -%}
Update partition tables of both nodes:
  cmd.run:
    - name: sleep 10; timeout -k 10 30 partprobe || true; ssh eosnode-2 "timeout -k 10 30 partprobe || true"

Update partition tables of primary node:
  cmd.run:
    - name: timeout -k 10 30 partprobe || true
{% endif %}
