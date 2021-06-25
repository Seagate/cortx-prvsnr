import re
import ipaddress
import argparse
from pathlib import Path
from cortx_setup.config import HW_TYPE, VM_TYPE
from provisioner.salt import cmd_run, local_minion_id


class CortxSetupError(Exception):
    pass


def host(hostname):
    result = True
    # TODO: Improve logic for validation of hostname
    hostname_regex = r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}$"
    if len(hostname) > 253:
        result = False
    else:
        if not re.search(hostname_regex, hostname):
            result = False
    if not result:
        raise argparse.ArgumentTypeError(f"Invalid fqdn {hostname}")
    return hostname


def ipv4(ip):
    if ip:
        value = ipaddress.IPv4Address(ip)
        # TODO : Improve logic internally convert ip to
        # canonical forms.
        if ip != str(value):
            raise argparse.ArgumentTypeError(
                f"Invalid IP address {ip} canonical form will be {value} ")
    return ip


def path(path):
    if path:
        if not Path(path).is_file():
            raise argparse.ArgumentTypeError(
                f"cannot access {path}: No such file ")
    return path


def interfaces(interface):
    for iface in interface:
        try:
            cmd_run(f"ip a | grep {iface}")
        except Exception as exc:
            raise CortxSetupError(f"Invalid interface {iface}\n {exc}")


def disk_devices(device_type, devices):
    local_devices = None
    if device_type == HW_TYPE:
        local_devices = cmd_run("multipath -ll|grep mpath|sort -k2|cut -d' ' -f1|sed 's|mpath|/dev/disk/by-id/dm-name-mpath|g'|paste -s -d, -")  # noqa: E501
        local_devices = local_devices[local_minion_id()]
        if not local_devices:
            raise CortxSetupError(f"Devices are not present on system")
        local_devices = local_devices.split(',')
    if device_type == VM_TYPE:
        local_devices = cmd_run("lsblk -o name -lpn | awk '/dev\/sd/{print}'")  # noqa: W605, E501
        local_devices = local_devices[local_minion_id()]
        if not local_devices:
            raise CortxSetupError(f"Devices are not present on system")
        local_devices = local_devices.split('\n')
    local_devices = set(local_devices)
    devices = set(devices)

    if not devices.issubset(local_devices):
        raise CortxSetupError(f"Invalid device list provided {devices}")
