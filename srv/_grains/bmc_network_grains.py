#!/usr/bin/python3
# vim: fenc=utf-8:ts=4:sw=4:sta:noet:sts=4:fdm=marker:ai

import logging
import re

# Import salt libs
import salt.utils.files
import salt.utils.path
import salt.utils.platform

# Solve the Chicken and egg problem where grains need to run before any
# of the modules are loaded and are generally available for any usage.
import salt.modules.cmdmod

__salt__ = {
    'cmd.run': salt.modules.cmdmod._run_quiet,
    'cmd.run_all': salt.modules.cmdmod._run_all_quiet
}

log = logging.getLogger(__name__)

def get_bmc_macs():
    '''
    returns a list of bmc ipv4 and mac addresses

    CLI:
    salt '*' grains.get stx:bmc
    salt '*' grains.get stx:bmc:port1_mac
    salt '*' grains.get stx:bmc:port1_ipv4

    A self test can be run by calling the script from a console:
        python ./stx:bmc_names.py
    '''

    ret = {'bmc_network': []}
    ipmitool=salt.utils.path.which('ipmitool')
    if not ipmitool:
        log.debug(
            'The ipmitool is not installed on this system.  '
            'BMC information will not be available.'
        )
        return ret
    for ipmi_port in range(1, 4):
        ipmi_ret = __salt__['cmd.run_all']([ipmitool, 'lan', 'print', ipmi_port])
        if ipmi_ret['retcode'] != 0:
            return ret
        for line in ipmi_ret['stdout'].splitlines():
            if line.startswith('MAC Address'):
                mac_std  = line.split()[3]
                mac_safe = mac_std.replace(':','_')
                mac_pxe  ='01-' + mac_std.replace(':','-')
                base_name = 'port' + str(ipmi_port) + '_mac'
                grain_name_std = base_name
                grain_name_safe= base_name + '_safe'
                grain_name_pxe = base_name + '_pxe'
                ret['bmc_network'].append({grain_name_std:  mac_std})
                ret['bmc_network'].append({grain_name_safe: mac_safe})
                ret['bmc_network'].append({grain_name_pxe:  mac_pxe})
            elif line.startswith('IP Address'):
                ipv4_std = line.split()[3]
                ipv4_safe = ipv4_std.replace('.','_')
                grain_name_std='port' + str(ipmi_port) + '_ipv4'
                grain_name_safe=grain_name_std + '_safe'
                ret['bmc_network'].append({grain_name_std: ipv4_std})
                ret['bmc_network'].append({grain_name_safe: ipv4_safe})
    return ret

if __name__ == "__main__":
    print get_bmc_macs()
