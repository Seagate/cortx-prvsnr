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
# salt-call saltutil.clear_cache && salt-call saltutil.sync_modules
# salt-call gluster.add_brick <volume> <brick>
# salt-call gluster.remove_brick <volume> <brick>
# salt-call gluster.is_brick_present <volume> <brick>
# salt-call gluster.remove_peer <hostname>

import sys


def add_brick(volume, brick):
    """ Add bricks to existing volume
    """
    __salt__ = getattr(sys.modules[__name__], '__salt__')
    res = __salt__["glusterfs.info"](volume)
    rep_cnt = res[volume]['replicaCount']

    if not rep_cnt:
        raise Exception("Failed to get replica for {volume}")

    rep_cnt = int(rep_cnt) + 1
    cmd = f"gluster volume add-brick {volume} replica {rep_cnt} {brick} force"
    res = __salt__["cmd.shell"](cmd)

    if not res:
        raise Exception("Failed to add brick {brick} to {volume}")

    return res


def remove_brick(volume, brick):
    """ Remove bricks to existing volume
    """
    __salt__ = getattr(sys.modules[__name__], '__salt__')
    res = __salt__["glusterfs.info"](volume)
    rep_cnt = res[volume]['replicaCount']

    if not rep_cnt:
        raise Exception("Failed to get replica for {volume}")

    rep_cnt = int(rep_cnt) - 1
    if rep_cnt < 1:
        raise Exception(
            "replica count should be greater than 0 in case of remove-brick")

    cmd = (f"echo 'y'|gluster volume remove-brick {volume}"
           f" replica {rep_cnt} {brick} force")
    res = __salt__["cmd.shell"](cmd)

    if not res:
        raise Exception("Failed to remove brick {brick} to {volume}")

    return res


def is_brick_present(volume, brick):
    """Check if brick present in volume
    """
    __salt__ = getattr(sys.modules[__name__], '__salt__')
    res = __salt__["glusterfs.info"](volume)
    bricks = res[volume]['bricks']
    is_present = False

    for brk, value in bricks.items():
        if brick in value['path']:
            is_present = True

    return is_present


def _detach_node(node):
    """Remove node from cluster
    """
    __salt__ = getattr(sys.modules[__name__], '__salt__')
    cmd = f"echo 'y'|gluster peer detach {node}"
    res = __salt__["cmd.shell"](cmd)
    return res


def remove_peer(node):
    """Remove bricks from this node and detach
       from cluster
    """
    __pillar__ = getattr(sys.modules[__name__], '__pillar__')
    volumes = __pillar__['glusterfs']['volumes']

    for volume in volumes:
        brick = f"{node}:{volume['export_dir']}"
        if is_brick_present(volume['name'], brick):
            remove_brick(volume['name'], brick)

    return _detach_node(node)
