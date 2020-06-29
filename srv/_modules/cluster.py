# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call cluster.nw_roaming_ip

import errno
import os
import subprocess
import sys
import yaml
import time
import provisioner

from shutil import copyfile

def storage_device_config():

    for node in __pillar__["cluster"]["node_list"]:
        if __pillar__["cluster"][node]["is_primary"]:
            cmd = "multipath -ll | grep prio=50 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"
        else:
            cmd = "multipath -ll | grep prio=10 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"

        device_list = []
        _timeout = 60
        _count = 0
        _sleep_time = 5
        while device_list == []:
            device_list = subprocess.Popen([cmd],
                                            shell=True,
                                            stdout=subprocess.PIPE
                                        ).stdout.read().decode("utf-8").splitlines()
            if device_list == []:
                if ( _count == 0 ):
                    print("[ INFO ] Waiting for multipath device to come up..")

                if ( _count >= _timeout ):
                    break
                else:
                    time.sleep(_sleep_time)
                    _tmp_cmd = "multipath -ll | grep prio=50 -B2|grep mpath | wc -l"
                    _mpath_devs = subprocess.Popen([_tmp_cmd],
                                                    shell=True,
                                                    stdout=subprocess.PIPE
                    ).stdout.read().decode("utf-8")

                    if ( int(_mpath_devs) > 0 ):
                        print("[ INFO ] Found multipath devices!")
                    else:
                        print(".")
                    _count = _count + _sleep_time

        if device_list == []:
            print ("[ ERROR ] multipath devices don't exist.")
            return False

        metadata_device = "/dev/disk/by-id/dm-name-{0}".format(device_list[0])
        data_field = "cluster/{0}/storage/data_devices".format(node)
        metadata_field = "cluster/{0}/storage/metadata_device".format(node)
        data_device = ["/dev/disk/by-id/dm-name-{0}".format(device) for device in device_list[1:]]

        provisioner.pillar_set(metadata_field, metadata_device)
        provisioner.pillar_set(data_field, data_device)

    return True


def nw_roaming_ip():

    for node in __pillar__["cluster"]["node_list"]:
        pvt_nw = __pillar__['cluster']['pvt_data_nw_addr']
        field = "cluster/{0}/network/data_nw/roaming_ip".format(node)
        roaming_ip = ("{0}.{1}").format('.'.join(pvt_nw.split('.')[:3]), int(node.split('-')[1]) + 2)
        if None == __pillar__["cluster"][node]["network"]["data_nw"]["roaming_ip"]:
            provisioner.pillar_set(field, roaming_ip)
        else:
            # Honour user override
            return True

    return True
