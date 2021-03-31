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

from typing import Union
from pathlib import Path
import logging
from packaging.version import Version

from .base import (
    ResourceParams, ResourceBase, ResourceState
)
from provisioner import config
from provisioner.vendor import attr
from provisioner.attr_gen import attr_ib

logger = logging.getLogger(__name__)


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


class ConsulParams(UpgradeParams):
    pass


@attr.s(auto_attribs=True)
class Consul(ResourceBase):
    resource_t_id = config.CortxResourceT.CONSUL
    params_t = ConsulParams


@attr.s(auto_attribs=True)
class ConsulState(ResourceState):
    resource_t = Consul


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
        if not (self.new_version > self.old_version):
            raise ValueError(
                f"New version '{self.new_version}' is less"
                f" than old one '{self.old_version}'"
            )
