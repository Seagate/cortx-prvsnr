# Do pre-checks
# -- if it is running as root (DONE)
# -- check raids (DONE)
# -- check that /boot is mounted on md0 (DONE)
# -- check LVM config (+-)
# -- whether the procedure has already been done (+-)
# Identify the correct volume (+-)
# Identify the disks (DONE)
# Do not forget to compare partitions sizes?? Create partitions??
# Unmount /boot/efi2 (DONE)
# Mount /boot/efi2 (DONE)
# Sync /boot/efi and /boot/efi2 (DONE)
# Setup perioric synchronization of /boot/efi and /boot/efi2
# Move md0 and md1
# Create swap partition on the second hard drive

from datetime import datetime
import subprocess
import sys
import re
from collections import namedtuple

ShResponse = namedtuple('ShResponse', 'stdout stderr')

def sh(command):
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

def strip_disk(disk_name) -> str:
  if disk_name.startswith("/dev/sd"):
    return re.sub('\d*$', '', disk_name)
  return disk_name

def get_partition(disk_name) -> str:
  if disk_name.startswith("/dev/sd"):
    return re.search(r'([0-9]+)$', disk_name).group(1)
  return None

### Queries

def query_multipath_devices():
  return ["/dev/mapper/" + x for x in sh_lines("multipath -ll -v 1").stdout]


def query_pvs_devices():
  raw_result = sh_lines(f"pvdisplay | grep 'PV Name'")
  if raw_result.stderr:
    return None

  result = []
  for line in raw_result.stdout:
    result.append(re.split(r'\s{2,}', line)[2])
  return result


def query_disk_uuid(disk):
  #if disk.startswith('/dev/dm') or disk.startswith('/dev/mapper'):
  #  return sh(f"sudo dmsetup info {disk} " + " | grep 'UUID:' | awk '{print $2}'").stdout.strip()
  #else:
   output = sh(f"blkid -p {disk}").stdout
   match = re.search(r'PARTUUID="([^\s]+)"', output)
   if match:
     return 'PARTUUID=' + match.group(1)
   match = re.search(r'PART_ENTRY_UUID="([^\s]+)"', output)
   if match:
     return 'PART_ENTRY_UUID=' + match.group(1)
   match = re.search(r'\sUUID="([^\s]+)"', output)
   if match:
     return 'UUID=' + match.group(1)
   return None


class RaidArray:
  name: str

  def __init__(self, name):
    self.name = name

  @property
  def devices(self):
    result_devices = sh_lines(f"mdadm -Q --detail {self.name} |  grep -A 10 'RaidDevice' | tail -n +2")
    devices = []
    for device_line in result_devices.stdout:
      columns = re.split(r'\s{2,}', device_line)
      devices.append({
        "raid_device": columns[4],
        "state": columns[5],
        "device": columns[6]
      })
    return devices

  @property
  def state(self):
    result_state = sh(f"mdadm -Q --detail {self.name} | grep 'State'")
    if result_state.stderr:
      return None

    return re.search(r':\s+([^\s]+)\s', result_state.stdout).group(1)

  @property
  def array_size(self):
    result_size = sh(f"mdadm -Q --detail {self.name} | grep 'Array Size'")
    if result_size.stderr:
      return None

    return re.search(r':\s+([0-9]+)\s', result_size.stdout).group(1)

  def ensure_valid(self, required_device_no):
    state = self.state
    ensure(state, f"{self.name} must be present")
    ensure(state in ['active', 'clean'], f"{self.name} must be clean or active")
    ensure(len(self.devices) == required_device_no, f"{self.name} must have exactly {required_device_no} raid devices")

  def filter_devices(self, device_name):
    return [x["device"] for x in self.devices if strip_disk(x["device"]) == strip_disk(device_name)]

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
  @property
  def mounts_list(self):
    raw_result = sh_lines("cat /proc/mounts")
    if raw_result.stderr:
      return None

    result = []
    for line in raw_result.stdout:
      columns = re.split(r'\s+', line)
      result.append({ "device": columns[0], "mount_point": columns[1] })
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

  @staticmethod
  def query_partitions(disk):
    raw_result = sh_lines(f"parted --machine -s {disk} unit B print | tail -n +3")
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


### Script routines

def resolve_partitions(primary_disk, enclosure_disk):
  """
  Ideally this function must also take care of re-partitioning the enclosure disk
  """

  primary_disk_partitions = PartitionList.query_partitions(primary_disk)
  enclosure_partitions = PartitionList.query_partitions(enclosure_disk)

  efi_partition = get_partition(efi_disk)
  boot_partition = get_partition(md0.filter_devices(primary_disk)[0])
  lvm_partition = get_partition(md1.filter_devices(primary_disk)[0])

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


def move_boot_efi(primary_id, enclosure_id):
  fstab_mgr = FstabManager()
  mount_mgr = MountManager()

  mount_mgr.unmount('/boot/efi2')
  fstab_mgr.unmount('/boot/efi2')
  
  sh(f"mkdosfs -F 16 {enclosure_id}")
  
  info(f"Mounting /boot/efi2 at {enclosure_id}")
  fstab_mgr.mount(enclosure_id, '/boot/efi2', 'vfat', fs_mntops='umask=0077')
  mount_mgr.reload_mounts()
  
  sh("rsync -acHAX /boot/efi/* /boot/efi2/")
  info(f"/boot/efi/ synchronization is complete")
  # TODO: set up a regular task for /boot/efi and /boot/efi2 synchronization


def move_raid_partition(raid_array, primary_id, secondary_disk, enclosure_id):
  return

  info(f"Removing old disks from {raid_array.name}") 
  for secondary_id in raid_array.filter_devices(secondary_disk):
    raid_array.fail_device(secondary_id)
    raid_array.remove_device(secondary_id)

  info(f"Adding {enclosure_id} to {raid_array.name}")
  raid_array.zero_superblock(enclosure_id)
  raid_array.add_device(enclosure_id)
  # TODO: wait until the synchronization is complete


def setup_swap(secondary_disk):
  # re-partition the secondary disk
  # set up swap (persistently)
  pass


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

primary_disk = strip_disk(efi_disk)
secondary_disk = strip_disk(efi2_disk)

info(f"Primary HDD: {primary_disk}")
info(f"Secondary HDD: {secondary_disk}")

ensure(md0.filter_devices(primary_disk), "Disk with /boot/efi must be included in /dev/md0")
#ensure(md0.filter_devices(secondary_disk), "Disk with /boot/efi2 must be included in /dev/md0")
ensure(md1.filter_devices(primary_disk), "Disk with /boot/efi must be included in /dev/md1")
#ensure(md1.filter_devices(secondary_disk), "Disk with /boot/efi2 must be included in /dev/md1")

# TODO: implement the disk-picking algorithm
enclosure_disk = query_multipath_devices()[0]
info(f"Target enclosure disk: {enclosure_disk}")

partitions = resolve_partitions(primary_disk, enclosure_disk)

fstab_mgr = FstabManager()
fstab_mgr.backup_fstab()

info("Moving /boot/efi2 partition")
move_boot_efi(primary_disk + partitions["efi"][0], enclosure_disk + partitions["efi"][1])

info("Moving /boot partition")
move_raid_partition(md0, primary_disk + partitions["boot"][0],
  secondary_disk,
  enclosure_disk + partitions["boot"][1])

info("Moving LVM partition")
move_raid_partition(md1, primary_disk + partitions["lvm"][0],
  secondary_disk,
  enclosure_disk + partitions["lvm"][1])

info(f"Settting up swap on {secondary_disk}")
# TODO: remove swap from the primary drive as well?
setup_swap(secondary_disk)

