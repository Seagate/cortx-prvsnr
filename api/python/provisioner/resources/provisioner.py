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
from provisioner.values import UNCHANGED

from .base import (
    ResourceParams, ResourceBase, ResourceState
)


logger = logging.getLogger(__name__)


class ProvisionerParams(ResourceParams):
    install_dir: Union[str, Path] = attr_ib(
        'path_resolved',
        cli_spec='provisioner/install_dir',
        special_values=[UNCHANGED],
        default=UNCHANGED
    )
    repo_tgz: Union[str, Path] = attr_ib(
        'path_exists',
        cli_spec='provisioner/repo/tgz',
        default=None
    )
    repo: Union[str, Path] = attr_ib(
        'path_exists',
        cli_spec='provisioner/repo/path',
        default=config.PROJECT_PATH
    )
    repo_version: str = attr_ib(
        cli_spec='provisioner/repo/version',
        converter=(lambda v: v if v else config.REPO_VERSION_RAW),
        default=None
    )


@attr.s(auto_attribs=True)
class Provisioner(ResourceBase):
    resource_t_id = config.CortxResourceT.PROVISIONER
    params_t = ProvisionerParams


@attr.s(auto_attribs=True)
class ProvisionerState(ResourceState):
    resource_t = Provisioner


@attr.s(auto_attribs=True)
class ProvisionerInstall(ProvisionerState):
    name = 'install'


@attr.s(auto_attribs=True)
class ProvisionerInstallLocal(ProvisionerState):
    name = 'install-local'
    install_dir: Union[str, Path] = ProvisionerParams.install_dir
    repo_tgz: Union[str, Path] = ProvisionerParams.repo_tgz
    repo_path: Union[str, Path] = ProvisionerParams.repo
    repo_version: str = ProvisionerParams.repo_version

# PROVISIONER API #

# TODO validator / converter etc.
class ProvisionerAPIParams(ResourceParams):
    # TODO better to use different sources, e.g.
    #      pip index, system pkg, provisioner installation from /opt etc.
    api_distr: str = attr_ib(
        cli_spec='provisioner/api/distr', default='pkg'
    )


@attr.s(auto_attribs=True)
class ProvisionerAPI(ResourceBase):
    resource_t_id = config.CortxResourceT.PROVISIONER_API
    params_t = ProvisionerAPIParams


@attr.s(auto_attribs=True)
class ProvisionerAPIState(ResourceState):
    resource_t = ProvisionerAPI


@attr.s(auto_attribs=True)
class ProvisionerAPIInstall(ProvisionerAPIState):
    name = 'install'
    api_distr: str = ProvisionerAPIParams.api_distr
