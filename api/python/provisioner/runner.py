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

import os
from typing import Union, Any, List

from .vendor import attr
from . import inputs
from .salt import provisioner_cmd
from .errors import ProvisionerError


# TODO TESTS
@attr.s(auto_attribs=True)
class SimpleRunner:
    commands: List
    nowait: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "run the command as a salt job in async mode"
            }
        }, default=False
    )

    @classmethod
    def fill_parser(cls, parser):
        inputs.ParserFiller.fill_parser(cls, parser)

    @classmethod
    def extract_positional_args(cls, kwargs):
        return inputs.ParserFiller.extract_positional_args(cls, kwargs)

    # TODO TYPING
    def run(self, command: Union[str, Any], *args, **kwargs):

        # TODO DOCS environment variable
        # TODO use config instead of (or in addition to) env variable

        # TODO IMPROVE
        salt_job = (
            (command != 'get_result') and
            (self.nowait or (os.getenv('PRVSNR_SALT_JOB', 'no') == 'yes'))
        )

        if salt_job:
            try:
                return provisioner_cmd(
                    command,
                    fun_args=args,
                    fun_kwargs=kwargs,
                    nowait=self.nowait
                )
            except ProvisionerError:
                raise
            except Exception as exc:
                raise ProvisionerError(repr(exc)) from exc
        else:
            cmd = self.commands[command]
            return cmd.run(*args, **kwargs)
