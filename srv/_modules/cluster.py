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
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call cluster.nw_roaming_ip

# Standard packages
import errno
import json
import logging
import os
import sys
import time

from shutil import copyfile

# Update PYTHONPATH to include Provisioner API installed at:
# /usr/local/lib/python3.6/site-packages/cortx-prvsnr-*
sys.path.append(os.path.join('usr','local','lib', 'python3.6', 'site-packages'))

# Cortx packages
import provisioner

logger = logging.getLogger(__name__)


def storage_device_config():

    server_nodes = [
        node for node in provisioner.pillar_get("cluster").keys()
        if "srvnode-" in node
    ]
    for node in server_nodes:
        cluster_dict = provisioner.pillar_get(f"cluster/{node}/roles", targets=node)
        if "primary" in cluster_dict[node][f"cluster/{node}/roles"]:
            cmd = "multipath -ll | grep prio=50 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"
        else:
            cmd = "multipath -ll | grep prio=10 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"

        device_list = []
        _timeout = 60
        _count = 0
        _sleep_time = 5
        while device_list == []:
            if ( _count == 0 ):
                logger.info(f"[ INFO ] Attempt {_count} Waiting for multipath device to come up...")

            if ( _count > _timeout ):
                msg = ("[ ERROR ] multipath devices don't exist. "
                        f"Giving up after {_timeout} second.")
                raise Exception(msg)
                # break
                # return False
            else:
                time.sleep(_sleep_time)

                logger.info(f"Command to populate multipath devices: {cmd}")
                device_list = __utils__['process.simple_process'](cmd)

                if ( len(device_list) > 0 ):
                    logger.info("[ INFO ] Found multipath devices...")
                else:
                    print(".")
                _count = _count + _sleep_time

        if device_list == []:
            raise Exception("[ ERROR ] multipath devices don't exist.")
            # return False

        metadata_devices = list()
        metadata_devices.append(f"/dev/disk/by-id/dm-name-{device_list[0]}")
        metadata_field = f"cluster/{node}/storage/metadata_devices".format(node)
        provisioner.pillar_set(metadata_field, metadata_devices)
        
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
    _metadata_field = "cluster/{0}/storage/metadata_devices".format(_target_node)

    _cmd = "multipath -ll | grep mpath | sort -k2.2 | awk '{ print $1 }'"
    _device_list = __utils__['process.simple_process'](_cmd) 

    metadata_devices = ["/dev/disk/by-id/dm-name-{0}".format(_device_list[0])]
    data_device = ["/dev/disk/by-id/dm-name-{0}".format(device) for device in _device_list[1:]]

    provisioner.pillar_set(_metadata_field, metadata_devices)
    provisioner.pillar_set(_data_field, data_device)
    return True
