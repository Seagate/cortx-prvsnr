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

import logging
from typing import Type

from provisioner.vendor import attr
from provisioner import config, inputs
from provisioner.attr_gen import attr_ib

from provisioner.commands._basic import (
    CommandParserFillerMixin,
)
from provisioner.commands.upgrade import GetSWUpgradeInfo
from provisioner.salt import StateFunExecuter

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SetReleaseVersionRunArgs:
    release: str = attr_ib(cli_spec='release/version', default=None)


@attr.s(auto_attribs=True)
class SetReleaseVersion(CommandParserFillerMixin):
    description = (
        "A command to set CORTX release."
    )

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = SetReleaseVersionRunArgs

    def run(self, release=None):
        if release is None:
            release = GetSWUpgradeInfo.cortx_version()

        if release:
            url = GetSWUpgradeInfo.get_release_info_url()
            source = (url.path if url.is_local() else str(url))
        else:
            logger.info(
                'No upgrade release is found, setting the factory one'
            )
            source = config.CORTX_RELEASE_FACTORY_INFO_PATH

        StateFunExecuter.execute(
            'file.managed',
            fun_kwargs=dict(
                name=config.CORTX_RELEASE_INFO_PATH,
                source=source,
                create=True,
                replace=True,
                user='root',
                group='root',
                mode=444
            )
        )
