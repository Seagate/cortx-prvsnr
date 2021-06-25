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

from provisioner.vendor import attr
from provisioner import config
from provisioner.attr_gen import attr_ib

from provisioner.commands._basic import (
    CommandParserFillerMixin,
)
from provisioner.salt import StateFunExecuter

from .release import CortxRelease

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SetRelease(CommandParserFillerMixin):
    description = (
        "A command to set CORTX release."
    )

    release: str = attr_ib(cli_spec='release/version')

    def run(self):
        url = CortxRelease(version=self.release).metadata_uri
        logger.debug(f"Found url '{url}' for the release '{self.release}'")

        StateFunExecuter.execute(
            'file.managed',
            fun_kwargs=dict(
                name=str(config.CORTX_RELEASE_INFO_PATH),
                source=(url.path if url.is_local else str(url)),
                skip_verify=True,
                create=True,
                replace=True,
                user='root',
                group='root',
                mode=444
            )
        )
