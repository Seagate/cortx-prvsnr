# File still work in progress as disks devices are hard coded

# This formula is an attempt to automate the raid setup on concerned devices.

# Setup raid on identified devices
setup_mdraid:
  raid.present:
    - name: /dev/md0
    - level: 1
    - devices:
      # identifying of disks should be automated
      - /dev/sdbt
      - /dev/sdbu

# Label raid disk partition created above
label_partition:
  module.run:
    - parted.mklabel:
      - device: /dev/md0
      - label_type: gpt

# Create raid partition for [SWAP]
make_swap_partition:
  module.run:
    - parted.mkpart:
      - device: /dev/md0
      - part_type: primary
      - fs_type: linux-swap
      - start: 0%
      - end: 35%

# Create raid partition of /opt
make_opt_partition:
  module.run:
    - parted.mkpart:
      - device: /dev/md0
      - part_type: primary
      - fs_type: ext4
      - start: 36%
      - end: 100%

# Print block device attributes
part1_blkid:
  module.run:
    - disk.blkid:
      - device: /dev/md0p1

# Print block device attributes
part2_blkid:
  module.run:
    - disk.blkid:
      - device: /dev/md0p2

# Activate SWAP device
mount_swap:
  mount.swap:
    - name: /dev/md0p1
    - persist: True     # save in the fstab

# Verify that a device is mounted
mount_opt_partition:
  mount.mounted:
    - name: /opt/seagate
    - device: /dev/md0p2
    - fstype: ext4
    - mkmnt: True       # create the mount point if it is otherwise not present
    - persist: True     # save in the fstab

# Was requried for some SSPL ticket: COSTOR-625
modify_mdadm_conf:
  cmd.run:
    - name: mdadm --detail --scan | tee /etc/mdadm.conf
    - unless: grep "$(mdadm --detail --scan)" /etc/mdadm.conf
