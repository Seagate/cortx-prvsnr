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

from provisioner import config
from provisioner.vendor import attr
from provisioner.attr_gen import attr_ib

from .base import (
    ResourceParams, ResourceBase, ResourceState
)

logger = logging.getLogger(__name__)


# XXX - default values depends on context (business logic),
#       e.g. might be UNCHANGED or a real current value
class CortxReposParams(ResourceParams):
    # TODO EOS-12076 validate it is a file or dir or url
    cortx: Union[str, Path] = attr_ib(
        'path_exists',
        cli_spec='repos/cortx',
        # FIXME allow url as well
        # XXX copy validation routine from SetSWUpdateRepo
    )
    dist_type: config.DistrType = attr_ib(
        cli_spec='repos/dist_type',
        default=config.DistrType.BUNDLE.value,
        # TODO EOS-12076 better validation
        converter=config.DistrType
    )
    deps: Union[str, Path] = attr_ib(
        'path_exists',
        cli_spec='repos/deps',
        default=None,
        # FIXME allow url as well
        # XXX copy validation routine from SetSWUpdateRepo
    )
    os: Union[str, Path] = attr_ib(
        'path_exists',
        cli_spec='repos/os',
        default=None,
        # FIXME allow url as well
        # XXX copy validation routine from SetSWUpdateRepo
    )
    py_index: bool = attr_ib(
        cli_spec='repos/py_index',
        default=False
    )


@attr.s(auto_attribs=True)
class CortxRepos(ResourceBase):
    resource_t_id = config.CortxResourceT.REPOS
    params_t = CortxReposParams


@attr.s(auto_attribs=True)
class CortxReposState(ResourceState):
    resource_t = CortxRepos


@attr.s
class CortxReposSetup(CortxReposState):
    name = 'setup'

    dist_type = CortxReposParams.dist_type
    cortx = CortxReposParams.cortx
    deps = CortxReposParams.deps
    os = CortxReposParams.os
    py_index = CortxReposParams.py_index

    target_build: Path = attr_ib(
        init=False, default=None
    )

    # XXX - for UNCHANCGED values we may resolve real values here
    #       and validate only after that
    def __attrs_post_init__(self):  # noqa: C901
        # TODO check that ISOs are not the same

        if self.dist_type == config.DistrType.BUNDLE:
            self.target_build = (
                'file://{}'.format(
                    config.PRVSNR_CORTX_REPOS_BASE_DIR /
                    config.CORTX_SINGLE_ISO_DIR
                )
            )
        else:
            if self.cortx is ('ISO' or 'dir'):  # FIXME
                self.target_build = 'file://{}'.format(
                    config.PRVSNR_CORTX_REPOS_BASE_DIR /
                    config.CORTX_ISO_DIR
                )
            else:  # url
                self.target_build = self.cortx
