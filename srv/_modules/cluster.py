#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing, 
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

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


# Commenting this code as it is causing controller issues due to controller shutdown
# def storage_device_config():

#     _target_node = __grains__['id']
#     _cluster_type = __pillar__["cluster"]["type"]

#     _ffile_path = '/opt/seagate/cortx/provisioner/generated_configs/{0}.cc'.format(_target_node)
#     _cc_flag = False

#     _cmd_mpath1 = "multipath -ll | grep -E \"prio=50|prio=10\" | wc -l"
#     _cmd_mpath2 = "multipath -ll | grep mpath | wc -l"


#     device_list = []
#     _timeout = 60
#     _count = 0
#     _sleep_time = 5
#     device_list = subprocess.Popen([_cmd_mpath2],
#                                 shell=True,
#                                 stdout=subprocess.PIPE
#                             ).stdout.read().decode("utf-8").splitlines()

#     while device_list == []:
#         if ( _count == 0 ):
#             print("[ INFO ] Waiting for multipath device to come up..", end="", flush=True)
#         else:
#             print(".", end="", flush=True)

#         if ( _count >= _timeout ):
#             break
#         else:
#             time.sleep(_sleep_time)
#             _mpath_devs_n = subprocess.Popen([_cmd_mpath2],
#                                             shell=True,
#                                             stdout=subprocess.PIPE
#             ).stdout.read().decode("utf-8")

#             if ( int(_mpath_devs_n) > 0 ):
#                 print("[ INFO ] Found multipath devices!")
#                 break

#             _count = _count + _sleep_time

#     if device_list == []:
#         print ("[ ERROR ] No multipath devices found.")
#         return False

#     _prio_lines = int(subprocess.getoutput(_cmd_mpath1))
#     _mpath_devs_n = int(subprocess.getoutput(_cmd_mpath2))

#     if _mpath_devs_n * 2 == _prio_lines and _cluster_type == "dual":
#         #The setup is cross connected to storage enclosure
#         _cc_flag = True

#     if _cc_flag == True:
#         # Setup is cross connected.
#         print('INFO: setup is cross connected')
#         _cc_flag = True
#         _ctrl_a_ip = __pillar__["storage_enclosure"]["controller"]["primary_mc"]["ip"]
#         _ctrl_user = __pillar__["storage_enclosure"]["controller"]["user"]
#         _ctrl_passwd = __pillar__["storage_enclosure"]["controller"]["secret"]
#         _ctrl_cli = "/opt/seagate/cortx/provisioner/srv/components/controller/files/scripts/controller-cli.sh"

#         # Shutdown controller B
#         print('INFO: Shutting down controller B')
#         _ctrl_cmd = "sh {0} host -h {1} -u {2} -p {3} --shutdown-ctrl b".format(_ctrl_cli, _ctrl_a_ip, _ctrl_user, _ctrl_passwd)
#         _ret = subprocess.Popen([_ctrl_cmd],
#                                     shell=True,
#                                     stdout=subprocess.PIPE
#                                     ).stdout.read().decode("utf-8").splitlines()
#         time.sleep(30)
#     else:
#         print('INFO: setup is not cross connected')

#     for node in __pillar__["cluster"]["node_list"]:
#         if __pillar__["cluster"][node]["is_primary"]:
#             cmd = "multipath -ll | grep prio=50 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"
#         else:
#             cmd = "multipath -ll | grep prio=10 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"

#         device_list = subprocess.Popen([cmd],
#                                         shell=True,
#                                         stdout=subprocess.PIPE
#                                     ).stdout.read().decode("utf-8").splitlines()
#         metadata_device = ["/dev/disk/by-id/dm-name-{0}".format(device_list[0])]
#         data_field = "cluster/{0}/storage/data_devices".format(node)
#         metadata_field = "cluster/{0}/storage/metadata_device".format(node)
#         data_device = ["/dev/disk/by-id/dm-name-{0}".format(device) for device in device_list[1:]]

#         provisioner.pillar_set(metadata_field, metadata_device)
#         provisioner.pillar_set(data_field, data_device)
#         if _cc_flag == True:
#             _ffile_path = '/opt/seagate/cortx/provisioner/generated_configs/{0}.cc'.format(node)
#             _cmd = "ssh {0} \"mkdir -p /opt/seagate/cortx/provisioner/generated_configs/; touch {1}\"".format(node, _ffile_path)
#             os.system(_cmd)

#     if _cc_flag == True:
#         print('INFO: Restarting the controller B')
#         _ctrl_cmd = "sh {0} host -h {1} -u {2} -p {3} --restart-ctrl b".format(_ctrl_cli, _ctrl_a_ip, _ctrl_user, _ctrl_passwd)
#         _ret = subprocess.Popen([_ctrl_cmd],
#                                     shell=True,
#                                     stdout=subprocess.PIPE
#                                     ).stdout.read().decode("utf-8").splitlines()
#         time.sleep(180)
#     return True


def storage_device_config():

    for node in provisioner.pillar_get("cluster/node_list"):
        if provisioner.pillar_get(f"cluster/{node}/is_primary"):
            cmd = "multipath -ll | grep prio=50 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"
        else:
            cmd = "multipath -ll | grep prio=10 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"

        device_list = []
        _timeout = 60
        _count = 0
        _sleep_time = 5
        while device_list == []:
            if ( _count == 0 ):
                print(f"[ INFO ] Attempt {_count} Waiting for multipath device to come up...")

            if ( _count > _timeout ):
                msg = ("[ ERROR ] multipath devices don't exist. "
                        f"Giving up after {_timeout} second.")
                raise Exception(msg)
                # break
                # return False
            else:
                time.sleep(_sleep_time)
                device_list = subprocess.Popen([cmd],
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE
                                    ).stdout.read().decode("utf-8").splitlines()

                if ( len(device_list) > 0 ):
                    print("[ INFO ] Found multipath devices...")
                else:
                    print(".")
                _count = _count + _sleep_time

        if device_list == []:
            raise Exception("[ ERROR ] multipath devices don't exist.")
            # return False

        metadata_device = list()
        metadata_device.append(f"/dev/disk/by-id/dm-name-{device_list[0]}")
        metadata_field = f"cluster/{node}/storage/metadata_device".format(node)
        provisioner.pillar_set(metadata_field, metadata_device)
        
        data_device = [f"/dev/disk/by-id/dm-name-{device}" for device in device_list[1:]]
        data_field = f"cluster/{node}/storage/data_devices"
        provisioner.pillar_set(data_field, data_device)

    if (len(provisioner.pillar_get("cluster/srvnode-1/storage/data_devices"))
        != len(provisioner.pillar_get("cluster/srvnode-2/storage/data_devices"))):
        msg = ("[ ERROR ] multipath devices don't match for the 2 nodes. "
                "Can't proceed exiting...")
        raise Exception(msg)
        # return False

    return True


def jbod_storage_config():
    _target_node = __grains__['id']
    _data_field = "cluster/{0}/storage/data_devices".format(_target_node)
    _metadata_field = "cluster/{0}/storage/metadata_device".format(_target_node)

    _cmd = "multipath -ll | grep mpath | sort -k2.2 | awk '{ print $1 }'"
    _device_list = subprocess.Popen([_cmd],shell=True,stdout=subprocess.PIPE).stdout.read().decode("utf-8").splitlines()

    metadata_device = ["/dev/disk/by-id/dm-name-{0}".format(_device_list[0])]
    data_device = ["/dev/disk/by-id/dm-name-{0}".format(device) for device in _device_list[1:]]

    provisioner.pillar_set(_metadata_field, metadata_device)
    provisioner.pillar_set(_data_field, data_device)
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
