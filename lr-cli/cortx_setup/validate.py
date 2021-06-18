import re
import ipaddress
import argparse
from pathlib import Path


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
