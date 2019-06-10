{% set node = 'node_1' if grains['host'] == pillar['facts']['node_1']['fqdn'] else 'node_2' if grains['host'] == pillar['facts']['node_2']['fqdn'] else None %}

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
label_partition:
  module.run:
    - partition.mklabel:
      - device: {{ pillar['facts'][node]['metadata_device'] }}
      - label_type: gpt

# Create raid partition for [SWAP]
make_swap_partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['facts'][node]['metadata_device'] }}
      - part_type: primary
      - fs_type: linux-swap
      - start: 0%
      - end: 30%

# Create raid partition of /opt
make_metadata_partition:
  module.run:
    - partition.mkpartfs:
      - device: {{ pillar['facts'][node]['metadata_device'] }}
      - part_type: primary
      - fs_type: ext4
      - start: 31%
      - end: 100%

# Activate SWAP device
mount_swap:
  mount.swap:
    - name: {{ pillar['facts'][node]['metadata_device'] }}1
    - persist: True     # save in the fstab

# Verify that a device is mounted
mount_mero_partition:
  mount.mounted:
    - name: /var/mero
    - device: {{ pillar['facts'][node]['metadata_device'] }}2
    - fstype: ext4
    - mkmnt: True       # create the mount point if it is otherwise not present
    - persist: True     # save in the fstab
    - mount: True
