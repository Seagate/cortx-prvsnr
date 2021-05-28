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

from typing import List, Union
import logging

from provisioner import config

from provisioner.vendor import attr
from provisioner.attr_gen import attr_ib
from provisioner.values import UNCHANGED, _PrvsnrValue

from .base import (
    ResourceParams, ResourceBase, ResourceState
)

logger = logging.getLogger(__name__)


# SALT-STACK COMMON #

@attr.s(auto_attribs=True)
class SaltStack(ResourceBase):
    resource_t_id = config.CortxResourceT.SALTSTACK
    params_t = None


@attr.s(auto_attribs=True)
class SaltStackState(ResourceState):
    resource_t = SaltStack


@attr.s(auto_attribs=True)
class SaltStackRepo(SaltStackState):
    name = 'repo'


# SALT-MASTER #

class SaltMasterParams(ResourceParams):
    lvm2_first: bool = attr_ib(
        cli_spec='salt_master/lvm2_first', default=False
    )
    updated_keys: List[str] = attr_ib(
        cli_spec='salt_master/onchanges', default=attr.Factory(list)
    )
    onchanges: str = attr_ib(
        cli_spec='salt_master/onchanges', default='restart'
    )


@attr.s(auto_attribs=True)
class SaltMaster(ResourceBase):
    resource_t_id = config.CortxResourceT.SALT_MASTER
    params_t = SaltMasterParams


@attr.s(auto_attribs=True)
class SaltMasterState(ResourceState):
    resource_t = SaltMaster


@attr.s(auto_attribs=True)
class SaltMasterPrepare(SaltMasterState):
    name = 'prepare'


@attr.s(auto_attribs=True)
class SaltMasterInstall(SaltMasterState):
    name = 'install'
    lvm2_first: bool = SaltMasterParams.lvm2_first


@attr.s(auto_attribs=True)
class SaltMasterConfig(SaltMasterState):
    name = 'config'
    updated_keys: List[str] = SaltMasterParams.updated_keys
    onchanges: str = SaltMasterParams.onchanges


class SaltMasterStart(SaltMasterState):
    name = 'start'


@attr.s(auto_attribs=True)
class SaltMasterStop(SaltMasterState):
    name = 'stop'


# SALT-MINION #


class SaltMinionParams(ResourceParams):
    masters: Union[List[str], _PrvsnrValue] = attr_ib(
        cli_spec='salt_minion/masters', default=UNCHANGED
    )
    cluster_uuid: Union[str, _PrvsnrValue] = attr_ib(
        cli_spec='salt_minion/cluster_uuid', default=UNCHANGED
    )
    onchanges: str = attr_ib(
        cli_spec='salt_minion/onchanges', default='restart'
    )
    rediscover: bool = attr_ib(
        cli_spec='salt_minion/rediscover', default=False
    )


@attr.s(auto_attribs=True)
class SaltMinion(ResourceBase):
    resource_t_id = config.CortxResourceT.SALT_MINION
    params_t = SaltMinionParams


@attr.s(auto_attribs=True)
class SaltMinionState(ResourceState):
    resource_t = SaltMinion


@attr.s(auto_attribs=True)
class SaltMinionPrepare(SaltMinionState):
    name = 'prepare'


@attr.s(auto_attribs=True)
class SaltMinionInstall(SaltMinionState):
    name = 'install'


@attr.s(auto_attribs=True)
class SaltMinionConfig(SaltMinionState):
    name = 'config'
    masters: Union[List[str], _PrvsnrValue] = SaltMinionParams.masters
    cluster_uuid: Union[str, _PrvsnrValue] = SaltMinionParams.cluster_uuid
    onchanges: str = SaltMinionParams.onchanges
    rediscover: bool = SaltMinionParams.rediscover


class SaltMinionStart(SaltMinionState):
    name = 'start'


@attr.s(auto_attribs=True)
class SaltMinionEnsureReady(SaltMinionState):
    name = 'ensure-ready'


@attr.s(auto_attribs=True)
class SaltMinionStop(SaltMinionState):
    name = 'stop'


# SALT-CLUSTER #

class SaltClusterParams(ResourceParams):
    regen_keys: bool = attr_ib(
        cli_spec='salt_cluster/regen_keys', default=False
    )


@attr.s(auto_attribs=True)
class SaltCluster(ResourceBase):
    resource_t_id = config.CortxResourceT.SALT_CLUSTER
    params_t = None  # XXX


@attr.s(auto_attribs=True)
class SaltClusterState(ResourceState):
    resource_t = SaltCluster


@attr.s(auto_attribs=True)
class SaltClusterConfig(SaltClusterState):
    name = 'config'

    # salt-cluster params
    regen_keys: bool = SaltClusterParams.regen_keys
    # salt-masters params
    lvm2_first: bool = SaltMasterParams.lvm2_first
    onchanges_master: str = SaltMasterParams.onchanges
    # salt-minions params
    masters: Union[List[str], _PrvsnrValue] = SaltMinionParams.masters
    cluster_uuid: Union[str, _PrvsnrValue] = SaltMinionParams.cluster_uuid
    onchanges_minion: str = SaltMinionParams.onchanges
    rediscover: bool = SaltMinionParams.rediscover
