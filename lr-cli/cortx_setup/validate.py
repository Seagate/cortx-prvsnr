import re
import ipaddress
import argparse


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
