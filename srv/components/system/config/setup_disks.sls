{% set node = '' %}}

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

# Label raid disk partition created above
label_partition:
  module.run:
    - parted.mklabel:
      - device: /dev/{{ pillar[node]['disk_1'] }}
      - label_type: gpt

# Create raid partition for [SWAP]
make_swap_partition:
  module.run:
    - parted.mkpart:
      - device: /dev/{{ pillar[node]['disk_1'] }}1
      - part_type: primary
      - fs_type: linux-swap
      - start: 0%
      - end: 1T

# Create raid partition of /opt
make_opt_partition:
  module.run:
    - parted.mkpart:
      - device: /dev/{{ pillar[node]['disk_2'] }}2
      - part_type: primary
      - fs_type: ext4
      - start: 1T
      - end: 100%

# Activate SWAP device
mount_swap:
  mount.swap:
    - name: /dev/{{ pillar[node]['disk_1'] }}1
    - persist: True     # save in the fstab

# Verify that a device is mounted
mount_opt_partition:
  mount.mounted:
    - name: /var/mero
    - device: /dev/{{ pillar[node]['disk_2'] }}2
    - fstype: ext4
    - mkmnt: True       # create the mount point if it is otherwise not present
    - persist: True     # save in the fstab

# Was requried for some SSPL ticket: COSTOR-625
# modify_mdadm_conf:
#   cmd.run:
#     - name: mdadm --detail --scan | tee /etc/mdadm.conf
#     - unless: grep "$(mdadm --detail --scan)" /etc/mdadm.conf
