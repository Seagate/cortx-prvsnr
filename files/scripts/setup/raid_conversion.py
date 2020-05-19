# Do pre-checks
# -- if it is running as root (DONE)
# -- check raids (DONE)
# -- check that /boot is mounted on md0 (DONE)
# -- check LVM config (+-)
# -- whether the procedure has already been done (+-)
# Identify the correct volume
# Identify the disks (DONE)
# Do not forget to compare partitions sizes?? Create partitions??
# Unmount /boot/efi2
# Move md0 and md1
# Mount /boot/efi2 (permanently? via /etc/fstab?)
# Sync /boot/efi and /boot/efi2
# Set up a cron script for auto-sync
# Create swap partition on the second hard drive


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

### Helpers

def check_root() -> bool:
  return sh_lines("id -u").stdout[0] == "0"

def strip_disk(disk_name) -> str:
  if disk_name.startswith("/dev/sd"):
    return re.sub('\d*$', '', disk_name)
  return disk_name


### Queries

def query_mdadm(device_name):
  result_size = sh(f"mdadm -Q --detail {device_name} | grep 'Array Size'")
  if result_size.stderr:
    return None

  result_state = sh(f"mdadm -Q --detail {device_name} | grep 'State'")
  result_devices = sh_lines(f"mdadm -Q --detail {device_name} |  grep -A 10 'RaidDevice' | tail -n +2")

  devices = []
  for device_line in result_devices.stdout:
    columns = re.split(r'\s{2,}', device_line)
    devices.append({
      "raid_device": columns[4],
      "state": columns[5],
      "device": columns[6]
    })

  return {
    "array_size": re.search(r':\s+([0-9]+)\s', result_size.stdout).group(1),
    "state": re.search(r':\s+([^\s]+)\s', result_state.stdout).group(1),
    "devices": devices
  }
  
def query_pvs_devices():
  raw_result = sh_lines(f"pvdisplay | grep 'PV Name'")
  if raw_result.stderr:
    return None

  result = []
  for line in raw_result.stdout:
    result.append(re.split(r'\s{2,}', line)[2])
  return result

def query_mounts():
  raw_result = sh_lines("cat /proc/mounts")
  if raw_result.stderr:
    return None

  result = []
  for line in raw_result.stdout:
    columns = re.split(r'\s+', line)
    result.append({ "device": columns[0], "mount_point": columns[1] })
  return result

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
  return result

def query_multipath_devices():
  return [ "/dev/mapper/" + x for x in sh_lines("multipath -ll -v 1").stdout]

### Script

ensure(check_root(), "Script must be run by a root user")
md0 = query_mdadm("/dev/md0")
md1 = query_mdadm("/dev/md1")

ensure(md0, "/dev/md0 must be present")
ensure(md0["state"] in ['active', 'clean'], "/dev/md0 must be clean or active")
ensure(len(md0["devices"]) == 2, "/dev/md0 must have exactly two raid devices")

ensure(md1, "/dev/md1 must be present")
ensure(md1["state"] in ['active', 'clean'], "/dev/md1 must be clean or active")
ensure(len(md1["devices"]) == 2, "/dev/md1 must have exactly two raid devices")

pvs_devices = query_pvs_devices()
ensure('/dev/md1' in pvs_devices, "There must be a physical volume on /dev/md1")
ensure('/dev/md0' not in pvs_devices, "There must not be any physical volumes on /dev/md0")

mounts = query_mounts()
ensure(next(x["device"] for x in mounts if x["mount_point"]=='/boot') == "/dev/md0", "/boot must be mounted on /dev/md0")

efi_disk = next((x["device"] for x in mounts if x["mount_point"]=='/boot/efi'), None)
efi2_disk = next((x["device"] for x in mounts if x["mount_point"]=='/boot/efi2'), None)

info(f"/boot/efi is mounted on {efi_disk}")
info(f"/boot/efi2 is mounted on {efi2_disk}")

ensure(efi_disk, "/boot/efi must be mounted")
ensure(efi2_disk, "/boot/efi2 must be mounted")

primary_disk = strip_disk(efi_disk)
secondary_disk = strip_disk(efi2_disk)

info(f"Primary HDD: {primary_disk}")
info(f"Secondary HDD: {secondary_disk}")

ensure(any(strip_disk(x["device"]) == primary_disk for x in md0["devices"]), "Disk with /boot/efi must be included in /dev/md0")
ensure(any(strip_disk(x["device"]) == secondary_disk for x in md0["devices"]), "Disk with /boot/efi2 must be included in /dev/md0")
ensure(any(strip_disk(x["device"]) == primary_disk for x in md1["devices"]), "Disk with /boot/efi must be included in /dev/md1")
ensure(any(strip_disk(x["device"]) == secondary_disk for x in md1["devices"]), "Disk with /boot/efi2 must be included in /dev/md1")

# TODO: implement the disk-picking algorithm
enclosure_disk = query_multipath_devices()[0]
info(f"Target enclosure disk: {enclosure_disk}")

primary_disk_partitions = sorted(query_partitions(primary_disk), key=lambda k: k["size"])
enclosure_partitions = sorted(query_partitions(enclosure_disk), key=lambda k: k["size"])

# TODO: match partitions: firstly those without raid flag, then with raid falg
