# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call cluster.nw_roaming_ip

# Standard packages
import errno
import os
import subprocess
import sys
import time
import yaml

from shutil import copyfile

# Update PYTHONPATH to include Provisioner API installed at:
# /usr/local/lib/python3.6/site-packages/cortx-prvsnr-*
sys.path.append(os.path.join('usr','local','lib', 'python3.6', 'site-packages'))

# Cortx packages
import provisioner


def storage_device_config():

    _target_node = __grains__['id']
    _ffile_path = '/opt/seagate/cortx/provisioner/generated_configs/{0}.cc'.format(_target_node)
    _cc_flag = False

    _cmd_mpath1 = "multipath -ll | grep -E \"prio=50|prio=10\" | wc -l"
    _cmd_mpath2 = "multipath -ll | grep mpath | wc -l"
    _ret = subprocess.Popen([_cmd_mpath2],
                                shell=True,
                                stdout=subprocess.PIPE
                                ).stdout.read().decode("utf-8").splitlines()
    subprocess.Popen([_cmd_mpath2], shell=True, stdout=subprocess.PIPE)
    subprocess.Popen([_cmd_mpath2], shell=True, stdout=subprocess.PIPE)
    if os.path.isfile(_ffile_path):
        # Setup is cross connected.
        print('INFO: setup is cross connected')
        _cc_flag = True
        _ctrl_a_ip = __pillar__["storage_enclosure"]["controller"]["primary_mc"]["ip"]
        _ctrl_user = __pillar__["storage_enclosure"]["controller"]["user"]
        _ctrl_passwd = __pillar__["storage_enclosure"]["controller"]["secret"]
        _ctrl_cli = "/opt/seagate/cortx/provisioner/srv/components/controller/files/scripts/controller-cli.sh"
    else:
        print('INFO: setup is not cross connected')

    if _cc_flag == True:
        # Shutdown controller B
        # run controller_cli.sh host -h 'ip_addr' -u admin -p '!passwd' --shutdown-ctrl b
        print('INFO: Shutting down controller B')
        _ctrl_cmd = "sh {0} host -h {1} -u {2} -p {3} --shutdown-ctrl b".format(_ctrl_cli, _ctrl_a_ip, _ctrl_user, _ctrl_passwd)
        _ret = subprocess.Popen([_ctrl_cmd],
                                    shell=True,
                                    stdout=subprocess.PIPE
                                    ).stdout.read().decode("utf-8").splitlines()
        time.sleep(30)

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

        metadata_device = ["/dev/disk/by-id/dm-name-{0}".format(device_list[0])]
        data_field = "cluster/{0}/storage/data_devices".format(node)
        metadata_field = "cluster/{0}/storage/metadata_device".format(node)
        data_device = ["/dev/disk/by-id/dm-name-{0}".format(device) for device in device_list[1:]]

        provisioner.pillar_set(metadata_field, metadata_device)
        provisioner.pillar_set(data_field, data_device)

    if _cc_flag == True:
        print('INFO: Shutting down controller B')
        _ctrl_cmd = "sh {0} host -h {1} -u {2} -p {3} --restart-ctrl b".format(_ctrl_cli, _ctrl_a_ip, _ctrl_user, _ctrl_passwd)
        _ret = subprocess.Popen([_ctrl_cmd],
                                    shell=True,
                                    stdout=subprocess.PIPE
                                    ).stdout.read().decode("utf-8").splitlines()
        time.sleep(180)

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
