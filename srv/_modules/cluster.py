# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call cluster.nw_roaming_ip

import errno
import os
import subprocess
import yaml
import time

from shutil import copyfile


def storage_device_config():
    _pillar_path = '/opt/seagate/eos-prvsnr/pillar/user/groups/all/cluster.sls'
    if not os.path.exists(_pillar_path):
        _pillar_path = '/opt/seagate/eos-prvsnr/pillar/components/cluster.sls'
        if not os.path.exists(_pillar_path):
            print("[ERROR   ] Cluster file {0} doesn't exist.".format(_pillar_path))
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                _pillar_path
            )

    if not os.path.exists(_pillar_path + '.bak'):
        copyfile(_pillar_path, _pillar_path + '.bak')

    _pillar_dict = dict()
    with open(_pillar_path, 'r') as fd:
        _pillar_dict = yaml.safe_load(fd)

    for node in _pillar_dict["cluster"]["node_list"]:
        if _pillar_dict["cluster"][node]["is_primary"]:
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
                if (_count == 0):
                    print("[ INFO ] Waiting for multipath device to come up..")

                if (_count >= _timeout):
                    break
                else:
                    time.sleep(_sleep_time)
                    _tmp_cmd = "multipath -ll | grep prio=50 -B2|grep mpath | wc -l"
                    _mpath_devs = subprocess.Popen([_tmp_cmd],
                        shell=True,
                        stdout=subprocess.PIPE
                    ).stdout.read().decode("utf-8")

                    if (int(_mpath_devs) > 0):
                        print("[ INFO ] Found multipath devices!")
                    else:
                        print(".")
                    _count = _count + _sleep_time

        if device_list == []:
            print("[ ERROR ] multipath devices don't exist.")
            return False

        metadata_device = list()
        metadata_device.append("/dev/disk/by-id/dm-name-{0}".format(device_list[0]))
        _pillar_dict["cluster"][node]["storage"]["metadata_device"] = metadata_device
        data_device = ["/dev/disk/by-id/dm-name-{0}".format(device) for device in device_list[1:]]
        _pillar_dict["cluster"][node]["storage"]["data_devices"] = data_device

    with open(_pillar_path, 'w') as fd:
        yaml.dump(
            _pillar_dict,
            stream=fd,
            default_flow_style=False,
            canonical=False,
            width=1,
            indent=4
        )

    return True


def nw_roaming_ip():
    _pillar_path = '/opt/seagate/eos-prvsnr/pillar/components/cluster.sls'
    if not os.path.exists(_pillar_path):
        _pillar_path = '/opt/seagate/ees-prvsnr/pillar/components/cluster.sls'
        if not os.path.exists(_pillar_path):
            print("[ERROR   ] Cluster file {0} doesn't exist.".format(_pillar_path))
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                _pillar_path
            )

    if not os.path.exists(_pillar_path + '.bak'):
        copyfile(_pillar_path, _pillar_path + '.bak')

    _pillar_dict = dict()
    with open(_pillar_path, 'r') as fd:
        _pillar_dict = yaml.safe_load(fd)

    for node in _pillar_dict["cluster"]["node_list"]:
        pvt_nw = _pillar_dict['cluster']['pvt_data_nw_addr']
        roaming_ip = ("{0}.{1}").format('.'.join(pvt_nw.split('.')[:3]), int(node.split('-')[1]) + 2)
        if _pillar_dict["cluster"][node]["network"]["data_nw"]["roaming_ip"] is None:
            _pillar_dict["cluster"][node]["network"]["data_nw"]["roaming_ip"] = roaming_ip
        else:
            # Honour user override
            return True

    with open(_pillar_path, 'w') as fd:
        yaml.dump(
            _pillar_dict,
            stream=fd,
            default_flow_style=False,
            canonical=False,
            width=1,
            indent=4
        )

    return True
