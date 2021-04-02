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

from typing import Union, List
import logging
from packaging.version import Version
from ipaddress import IPv4Address

from .base import (
    ResourceParams, ResourceBase, ResourceState
)
from provisioner import config, attr_gen
from provisioner.vendor import attr
from provisioner.attr_gen import attr_ib

logger = logging.getLogger(__name__)


class VendorParamsMixin:
    vendored: bool = attr_ib(cli_spec='setup/vendored', default=False)


class UpgradeParams(ResourceParams):
    old_version: Union[str, Version] = attr_ib(
        'version', cli_spec='upgrade/old_version',
    )
    new_version: Union[str, Version] = attr_ib(
        'version', cli_spec='upgrade/new_version',
    )
    iteration: Union[str, int] = attr_ib(
        cli_spec='upgrade/iteration',
        default=0,
        converter=int
    )
    level: config.ConfigLevelT = attr_ib(
        cli_spec='upgrade/level',
        default=config.ConfigLevelT.NODE.value,
        converter=config.ConfigLevelT
    )


class ConsulParams(UpgradeParams, VendorParamsMixin):
    server: bool = attr_ib(cli_spec='consul/server', default=True)
    bind_addr: IPv4Address = attr_ib(
        'ipv4', cli_spec='consul/bind_addr', default='0.0.0.0'
    )
    # TODO List[ip4, domain] ???
    retry_join: List[str] = attr_ib(
        cli_spec='consul/retry_join', default=[]
    )
    version: Union[str, Version] = attr_ib(
        'version', cli_spec='consul/vendor/version', default=None,
        validator=attr.validators.optional(attr_gen.validator__version)
    )

    service: bool = attr_ib(init=False, default=True)


@attr.s(auto_attribs=True)
class Consul(ResourceBase):
    resource_t_id = config.CortxResourceT.CONSUL
    params_t = ConsulParams


@attr.s(auto_attribs=True)
class ConsulState(ResourceState):
    resource_t = Consul


@attr.s
class ConsulInstall(ConsulState):
    name = 'install'
    consul_version: Union[str, Version] = ConsulParams.version
    vendored: bool = ConsulParams.vendored


@attr.s
class ConsulConfig(ConsulState):
    name = 'config'

    server: bool = ConsulParams.server
    bind_addr: IPv4Address = ConsulParams.bind_addr
    retry_join: List[str] = ConsulParams.retry_join
    service: bool = ConsulParams.service


@attr.s
class ConsulStart(ConsulState):
    name = 'start'


@attr.s
class ConsulStop(ConsulState):
    name = 'stop'


@attr.s
class ConsulTeardown(ConsulState):
    name = 'teardown'


@attr.s
class ConsulUpgrade(ConsulState):
    name = 'upgrade'

    old_version = ConsulParams.old_version
    new_version = ConsulParams.new_version
    level = ConsulParams.level
    iteration = ConsulParams.iteration

    # XXX - for UNCHANCGED values we may resolve real values here
    #       and validate only after that
    def __attrs_post_init__(self):  # noqa: C901
        super().__attrs_post_init__()

        if not (self.new_version > self.old_version):
            raise ValueError(
                f"New version '{self.new_version}' is less"
                f" than old one '{self.old_version}'"
            )
