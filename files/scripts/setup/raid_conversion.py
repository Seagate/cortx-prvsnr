# TODO:
# -- Set up periodic /boot/efi and /boot/efi2 synchronization
# -- Check whether /var/mero is mounted on the chosen partition on the enclosure disk
# -- Finalize the procedure of the target enclosure disk selection

import subprocess
import sys
import re
import time
from datetime import datetime
from collections import namedtuple

ShResponse = namedtuple('ShResponse', 'stdout stderr')

def sh(command):
  print("\033[93m# " + command + "\033[0m")
  result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  return ShResponse(
    stderr=result.stderr.decode('utf-8'),
    stdout=result.stdout.decode('utf-8'))

def sh_lines(command):
  result = sh(command)
  return ShResponse(
    stderr=result.stderr.splitlines(),
    stdout=result.stdout.splitlines())

def ensure(condition, comment):
  if not condition:
    print(comment)
    sys.exit(1)

def info(comment):
  print(comment)

def debug(comment):
  print(comment)

### Helpers

def check_root() -> bool:
  return sh_lines("id -u").stdout[0] == "0"


class DeviceName:
  """ Represents a full disk name or a single partition. """
  PARTITION_PREFIXES = ["/dev/sd", "/dev/mapper/mpath"]

  def __init__(self, disk_name, partition=None):
    self.disk_name = self._normalize_name(disk_name)
    if partition and not self._query_partition(self.disk_name):
      self.disk_name = self.disk_name + str(partition)

  def __str__(self):
    return self.disk_name

  def __eq__(self, obj):
    if isinstance(obj, str):
      obj = DeviceName(obj)
    return self.disk_name == obj.disk_name

  @property
  def partition(self):
    """ Retrieves the partition number (if present) """
    return self._query_partition(self.disk_name)

  @property
  def disk(self):
    """ Returns the disk name without the partition number """
    if self.partition:
      return re.sub('\d*$', '', self.disk_name)
    else:
      return self.disk_name

  def _normalize_name(self, disk):
    """ If `disk` is a short device mapper link, retrieves the full name """
    disk_name = disk
    if isinstance(disk, DeviceName):
      disk_name = disk.disk_name
    elif disk_name.startswith('/dev/dm-'):
      result = sh(f"dmsetup info {disk_name} | grep 'Name:' "+"| awk '{print $2}'")
      if not result.stderr:
        disk_name = '/dev/mapper/' + result.stdout.strip()
    return disk_name

  def _query_partition(self, disk_name):
    if any(disk_name.startswith(x) for x in self.PARTITION_PREFIXES):
      match_result = re.search(r'([0-9]+)$', disk_name)
      if match_result:
        return match_result.group(1)
    return None


### Queries

def query_multipath_devices():
  return [DeviceName("/dev/mapper/" + x) for x in sh_lines("multipath -ll -v 1").stdout]


def query_pvs_devices():
  raw_result = sh_lines(f"pvdisplay | grep 'PV Name'")
  if raw_result.stderr:
    return None

  result = []
  for line in raw_result.stdout:
    result.append(DeviceName(re.split(r'\s{2,}', line)[2]))
  return result


class RaidArray:
  """ Represents a RAID array. Provides methods for RAID array management. """
  name: str

  def __init__(self, name):
    self.name = name
    # TODO: check whether the array exists

  @property
  def devices(self):
    result_devices = sh_lines(f"mdadm -Q --detail {self.name} |  grep -A 10 'RaidDevice' | tail -n +2")
    devices = []
    for device_line in result_devices.stdout:
      columns = re.split(r'\s{2,}', device_line)
      devices.append({
        "raid_device": columns[4],
        "state": columns[5],
        "device": DeviceName(columns[6])
      })
    return devices

  @property
  def state(self):
    result_state = sh(f"mdadm -Q --detail {self.name} | grep 'State :'")
    if result_state.stderr:
      return None
    return re.search(r':\s+([^\n]+)', result_state.stdout).group(1).strip()

  @property
  def array_size(self):
    result_size = sh(f"mdadm -Q --detail {self.name} | grep 'Array Size'")
    if result_size.stderr:
      return None
    return re.search(r':\s+([0-9]+)\s', result_size.stdout).group(1)

  @property
  def total_devices(self):
    result_size = sh(f"mdadm -Q --detail {self.name} | grep 'Total Devices'")
    if result_size.stderr:
      return None
    return int(re.search(r':\s+([0-9]+)\s', result_size.stdout).group(1))

  def ensure_valid(self, required_device_no):
    state = self.state
    ensure(state, f"{self.name} must be present")
    ensure(state in ['active', 'clean'], f"{self.name} must be clean or active")
    ensure(self.total_devices == required_device_no, f"{self.name} must have exactly {required_device_no} raid devices")

  def filter_devices(self, device_name):
    device = DeviceName(device_name)
    return [x["device"] for x in self.devices if x["device"].disk == device.disk]

  def fail_device(self, device_name):
    ensure(device_name in self.filter_devices(device_name), f"{device_name} must be included in {self.name}")
    result = sh(f"mdadm {self.name} --fail {device_name}")
    return not result.stderr

  def remove_device(self, device_name):
    result = sh(f"mdadm {self.name} --remove {device_name}")
    return not result.stderr

  def zero_superblock(self, device_name):
    result = sh(f"mdadm --zero-superblock {device_name}")
    return not result.stderr

  def add_device(self, device_name):
    result = sh(f"mdadm {self.name} -a {device_name}")
    return not result.stderr


class FstabManager:
  """ Provides operations with the /etc/fstab file """
  @property
  def fstab_list(self):
    lines = []
    with open('/etc/fstab') as f:
      for line in f.readlines():
        parsed = self.parse_line(line)
        if parsed:
          lines.append(parsed)
    return lines

  def parse_line(self, line):
    line = line.strip()
    if line.startswith('#'):
      return None
    columns = re.split(r'\s+', line)
    if len(columns) != 6:
      return None
    return {
      'fs_spec': columns[0],
      'fs_file': columns[1],
      'fs_vfstype': columns[2]
    }

  def create_line(self, fs_spec, fs_file, fs_vfstype,
                    fs_mntops='defaults', fs_freq='0', fs_passno='0'):
    return f"{fs_spec}\t{fs_file}\t\t{fs_vfstype}\t{fs_mntops}\t{fs_freq} {fs_passno}"

  def unmount(self, mount_point):
    new_contents = ''
    with open('/etc/fstab', 'r+') as f:
      for line in f.readlines():
        parsed = self.parse_line(line)
        if parsed and parsed['fs_file'] == mount_point:
          new_contents += '#'
        new_contents += line

      f.seek(0, 0)
      f.write(new_contents)
      f.truncate()

  def mount(self, fs_spec, fs_file, *args, **kwargs):
    new_line = self.create_line(fs_spec, fs_file, *args, **kwargs)
    if any(x['fs_file'] == fs_file for x in self.fstab_list):
      debug(f'Attempting to mount {fs_file} while it is already in /etc/fstab')
      return

    new_contents = ''
    with open('/etc/fstab', 'r+') as f:
      for line in f.readlines():
        parsed = self.parse_line(line)
        new_contents += line
      new_contents = new_contents.strip() + f"\n{new_line}\n"
      
      f.seek(0,0)
      f.write(new_contents)
      f.truncate()

  def backup_fstab(self):
    sh('cp -f /etc/fstab /etc/fstab.bak' + (datetime.now().isoformat()))


class MountManager:
  """ Provides device mount management """
  @property
  def mounts_list(self):
    raw_result = sh_lines("cat /proc/mounts")
    if raw_result.stderr:
      return None

    result = []
    for line in raw_result.stdout:
      columns = re.split(r'\s+', line)
      result.append({ "device": DeviceName(columns[0]), "mount_point": columns[1] })
    return result

  def is_mounted(self, mount_point):
    return self.query_device(mount_point) is not None

  def query_device(self, mount_point):
    return next((x["device"] for x in self.mounts_list if x["mount_point"] == mount_point), None)

  def mount(self, mount_point, device, fs):
    if self.is_mounted(mount_point):
      return False
    result = sh(f"mount -t {fs} -o fmask=0077,dmask=0077 {device} {mount_point}")
    return not result.stderr

  def unmount(self, mount_point):
    if self.is_mounted(mount_point):
      sh(f"umount {mount_point}")
      
  def reload_mounts(self):
    sh("mount -a")


class PartitionList:
  partitions = []
  def __init__(self, partitions):
    self.partitions = partitions

  def filter_by_number(self, ids):
    return PartitionList([x for x in self.partitions if x["number"] in ids])

  def filter_raid(self):
    return PartitionList([x for x in self.partitions if "raid" in x["flags"]])

  def filter_nonraid(self):
    return PartitionList([x for x in self.partitions if "raid" not in x["flags"]])

  def match_to(self, right_partitions) -> dict:
    """ Matches own partitions to same-sized partitions of `right_partitions` """
    debug(f"Matching {self.partitions} with {right_partitions.partitions}")

    right_tmp = right_partitions.partitions.copy()
    response = {}
    for left_partition in self.partitions:
      match = next((x for x in right_tmp if x["size"] == left_partition["size"]), None)
      if not match:
        return None
      response[left_partition["number"]] = match["number"]
      right_tmp.remove(match)
    return response


class PartitionManager:
  ALLOWED_LABEL_TYPES = ['gpt', 'msdos']
  ALLOWED_PART_TYPES = ['primary', 'extended', 'logical']
  def __init__(self, disk):
    self.disk = disk
    # TODO: validate that the disk exists

  def query_partitions(self):
    raw_result = sh_lines(f"parted --machine -s {self.disk} unit B print | tail -n +3")
    result = []
    for line in raw_result.stdout:
      columns = re.split(r':', re.sub('[\;]?$', '', line))
      result.append({
        "number": columns[0],
        "size": re.sub('[^\d]*$', '', columns[3]),
        "file_system": columns[4],
        "name": columns[5],
        "flags": columns[6]
      })
    return PartitionList(result)

  def mklabel(self, label_type):
    if label_type not in self.ALLOWED_LABEL_TYPES:
      raise Exception("Invalid label_type for mklabel")
    result = sh(f"parted -s {self.disk} mklabel {label_type}")
    return not result.stderr

  def mkpart(self, part_type, fs_type, start, end):
    if part_type not in self.ALLOWED_PART_TYPES:
      raise Exception("Invalid part_type")
    # TODO: validate the rest of args
    result = sh(f"parted -s {self.disk} mkpart {part_type} {fs_type} {start} {end}")
    return not result.stderr


### Script routines

def resolve_partitions(primary_disk, enclosure_disk, efi_partition):
  """
  Matches partitions of the primary disk to the partitions of the enclosure disk
  The partitions must have equal size
  """
  primary_disk_partitions = PartitionManager(primary_disk).query_partitions()
  enclosure_partitions = PartitionManager(enclosure_disk).query_partitions()

  boot_partition = md0.filter_devices(primary_disk)[0].partition
  lvm_partition = md1.filter_devices(primary_disk)[0].partition

  info(f"/boot/efi partition on {primary_disk}: {efi_partition}")
  info(f"/boot partition on {primary_disk}: {boot_partition}")
  info(f"LVM partition on {primary_disk}: {lvm_partition}")

  efi_match = primary_disk_partitions.filter_by_number([efi_partition]) \
    .match_to(enclosure_partitions.filter_nonraid())
  ensure(efi_match, "Cannot match /boot/efi partition")

  nonefi_match = primary_disk_partitions.filter_by_number([boot_partition, lvm_partition]) \
    .match_to(enclosure_partitions.filter_raid())
  ensure(nonefi_match, "Cannot match /boot and LVM partitions")

  encl_efi_partition = efi_match[efi_partition]
  encl_boot_partition = nonefi_match[boot_partition]
  encl_lvm_partition = nonefi_match[lvm_partition]

  info(f"/boot/efi will be placed on partition {encl_efi_partition} of {enclosure_disk}")
  info(f"/boot will be placed on partition {encl_boot_partition} of {enclosure_disk}")
  info(f"LVM will be placed on partition {encl_lvm_partition} of {enclosure_disk}")

  return {
    "efi": [efi_partition, encl_efi_partition],
    "boot": [boot_partition, encl_boot_partition],
    "lvm": [lvm_partition, encl_lvm_partition]
  }


def move_boot_efi(enclosure_location):
  """ Moves /boot/efi2 to the `enclosure_location` """
  fstab_mgr = FstabManager()
  mount_mgr = MountManager()

  mount_mgr.unmount('/boot/efi2')
  fstab_mgr.unmount('/boot/efi2')
  
  sh(f"mkdosfs -F 16 {enclosure_location}")
  
  info(f"Mounting /boot/efi2 at {enclosure_location}")
  fstab_mgr.mount(enclosure_location, '/boot/efi2', 'vfat', fs_mntops='umask=0077')
  mount_mgr.reload_mounts()
  
  sh("rsync -acHAX /boot/efi/* /boot/efi2/")
  info(f"/boot/efi/ synchronization is complete")
  # TODO: set up a regular task for /boot/efi and /boot/efi2 synchronization


def move_raid_partition(raid_array, secondary_location, enclosure_location):
  """ 
     Removes `secondary_location` from `raid_array`
     Replaces it with `enclosure_location`
  """
  info(f"Removing old disks from {raid_array.name}")
  for secondary_id in raid_array.filter_devices(secondary_location):
    info(f".. removing {secondary_id}")
    raid_array.fail_device(secondary_id)
    raid_array.remove_device(secondary_id)

  info(f"Adding {enclosure_location} to {raid_array.name}")
  raid_array.zero_superblock(enclosure_location)
  raid_array.add_device(enclosure_location)
  info(f"Waiting for rebuild to complete..")
  
  time.sleep(5)
  while "recovering" in raid_array.state:
    time.sleep(15)
  info(f"Rebuilding is complete")


def setup_swap(disk):
  """
     Turns `disk` into a swap
  """
  info(f"Re-partitioning {disk}")
  partition_mgr = PartitionManager(disk)
  partition_mgr.mklabel('gpt')
  partition_mgr.mkpart('primary', 'linux-swap', '0%', '100%')
  # TODO: check that the partition is indeed created and log it

  partition = DeviceName(disk, 1)
  info(f"Setting up swap on {partition}")
  sh(f"mkswap {partition}")
  sh(f"swapon -p 32767 {partition}")

  # TODO: check that swap has indeed been created
  fstab_mgr = FstabManager()
  fstab_mgr.mount(partition, 'none', 'swap', fs_mntops='defaults,pri=32767')

### Script 

# TODO: ensure that multipath is built into initramfs!!!

ensure(check_root(), "Script must be run by a root user")

md0 = RaidArray("/dev/md0")
md0.ensure_valid(2)

md1 = RaidArray("/dev/md1")
md1.ensure_valid(2)

pvs_devices = query_pvs_devices()
ensure('/dev/md1' in pvs_devices, "There must be a physical volume on /dev/md1")
ensure('/dev/md0' not in pvs_devices, "There must not be any physical volumes on /dev/md0")

mount_mgr = MountManager()
ensure(mount_mgr.query_device('/boot') == '/dev/md0', "/boot must be mounted on /dev/md0")

efi_disk = mount_mgr.query_device('/boot/efi')
efi2_disk = mount_mgr.query_device('/boot/efi2')

info(f"/boot/efi is mounted on {efi_disk}")
info(f"/boot/efi2 is mounted on {efi2_disk}")

ensure(efi_disk, "/boot/efi must be mounted")
ensure(efi2_disk, "/boot/efi2 must be mounted")

primary_disk = efi_disk.disk
secondary_disk = efi2_disk.disk

info(f"Primary HDD: {primary_disk}")
info(f"Secondary HDD: {secondary_disk}")

ensure(md0.filter_devices(primary_disk), "Disk with /boot/efi must be included in /dev/md0")
ensure(md0.filter_devices(secondary_disk), "Disk with /boot/efi2 must be included in /dev/md0")
ensure(md1.filter_devices(primary_disk), "Disk with /boot/efi must be included in /dev/md1")
ensure(md1.filter_devices(secondary_disk), "Disk with /boot/efi2 must be included in /dev/md1")

# TODO: implement the disk-picking algorithm
enclosure_disk = query_multipath_devices()[0]
info(f"Target enclosure disk: {enclosure_disk}")

partitions = resolve_partitions(primary_disk, enclosure_disk, efi_disk.partition)

fstab_mgr = FstabManager()
fstab_mgr.backup_fstab()


info("Moving /boot/efi2 partition")
move_boot_efi(DeviceName(enclosure_disk, partitions["efi"][1]))

info("Moving /boot partition")
move_raid_partition(md0, secondary_disk, DeviceName(enclosure_disk, partitions["boot"][1]))

info("Moving LVM partition")
move_raid_partition(md1, secondary_disk, DeviceName(enclosure_disk, partitions["lvm"][1]))

info(f"Settting up swap on {secondary_disk}")
# TODO: remove swap from the primary drive?
setup_swap(secondary_disk)

