{% set node = grains['id'] %}

# File still work in progress as disks devices are hard coded

# This formula is an attempt to automate the raid setup on concerned devices.

# Setup raid on identified devices
# setup_mdraid:
#   raid.present:
#     - name: /dev/md0
#     - level: 1
#     - devices:
#       # identifying of disks should be automated
#       - /dev/sdbt
#       - /dev/sdbu

# Was requried for some SSPL ticket: COSTOR-625
# modify_mdadm_conf:
#   cmd.run:
#     - name: mdadm --detail --scan | tee /etc/mdadm.conf
#     - unless: grep "$(mdadm --detail --scan)" /etc/mdadm.conf

# Label raid disk partition created above
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
      - end: 30%

# Create partition for Metadata
Create metadata partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - part_type: primary
      - fs_type: ext4
      - start: 30%
      - end: 100%

# Make SWAP
Make SWAP partition:
  cmd.run:
    - name: mkswap {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part1
    - onlyif: test -e {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part1
    - require:
      - module: Create swap partition


# Activate SWAP device
Enable swap:
  mount.swap:
    - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part1
    - persist: True     # save in the fstab
    - require:
      - cmd: Make SWAP partition

# Format metadata partition
Make metadata partition:
  module.run:
    - extfs.mkfs:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part2
      - fs_type: ext4
      - require:
        - module: Create metadata partition

# Ensure /var/mero is mounted
Mount mero partition:
  mount.mounted:
    - name: /var/mero
    - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part2
    - fstype: ext4
    - mkmnt: True       # create the mount point if it is otherwise not present
    - persist: True     # save in the fstab
    - mount: True
    - require:
      - module: Make metadata partition
