# Setup SWAP and /var/mero
{% set node = grains['id'] %}

Label Metadata partition:
  module.run:
    - partition.mklabel:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - label_type: gpt

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
    - partition.mkpartfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext4
      - start: 50%
      - end: 100%

Refresh partition:
  cmd.run:
    - name: blockdev --flushbufs /dev/disk/by-id/dm-name-mpath* || true
  module.run:
    - partition.probe: []

# Make SWAP
Ensure SWAP partition is unmounted:
  cmd.run:
    - name: swapoff -a && sleep 2

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

# Format metadata partition
Make metadata partition:
  module.run:
    - extfs.mkfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
      - fs_type: ext4
      - label: eos_metadata
      - require:
        - module: Create metadata partition
