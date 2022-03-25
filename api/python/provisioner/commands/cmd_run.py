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
from typing import Type

from . import RunArgs, CommandParserFillerMixin
from .. import inputs
from ..config import SUPPORTED_REMOTE_COMMANDS, ALL_MINIONS
from ..salt import function_run
from ..vendor import attr


# TODO IMPROVE EOS-14361 mask possible secrets in cmd_args and/or cmd_stdin
@attr.s(auto_attribs=True)
class CmdRunArgs:
    cmd_name: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': ("command to be run on target nodes. "
                         "Case sensitive")
            }
        }
    )
    cmd_args: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': ("string which represents command's "
                         "arguments and parameters")
            }
        },
        default=""  # empty string
    )
    cmd_stdin: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': ("string which represents command's stdin. "
                         "Can be used to pass username and passwords")
            }
        },
        default=""  # empty string
    )
    targets: str = RunArgs.targets
    dry_run: bool = RunArgs.dry_run


@attr.s(auto_attribs=True)
class CmdRun(CommandParserFillerMixin):
    """
    Base class to support remote commands run
    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = CmdRunArgs

    _PRV_METHOD_MOD = "_"  # private method modificator

    def _cortxcli(self, *, args: str, stdin: str, targets: str,
                  dry_run: bool = False):
        """
        Private method for `cortxcli` command.

        :param args: `cortxcli` specific command parameters and arguments
        :param stdin: `cortxcli` stdin parameters like username and password.
                      NOTE: Parameters should be '\n' new line seperated
        :param targets: target nodes where `cortxcli` command will be run
        :param bool dry_run: for debugging purposes. Run method without
                             real command run on target nodes
        :return:
        """

        if dry_run:
            return

        cmd_line = f'cortxcli {args}'

        # TODO: currently salt.cmd_run doesn't support named arguments `kwargs`
        return function_run("cmd.run", targets=targets, fun_args=[cmd_line],
                            fun_kwargs=dict(stdin=stdin))

    def run(self, cmd_name: str, cmd_args: str = "", cmd_stdin: str = None,
            targets: str = ALL_MINIONS, dry_run: bool = False):
        """
        Basic run method to run remote commands on targets nodes:

        :param str cmd_name: specific command to be run on target nodes
        :param str cmd_args: command specific arguments
        :param cmd_stdin: command specific stdin parameters like username and
                          password.
        :param str targets: target nodes where command is planned
                            to be run
        :param bool dry_run: for debugging purposes. Run method without
                             real command running on target nodes
        :return:
        """
        cmd = cmd_name.strip()

        if cmd in SUPPORTED_REMOTE_COMMANDS:
            return getattr(self, self._PRV_METHOD_MOD + cmd)(args=cmd_args,
                                                             targets=targets,
                                                             stdin=cmd_stdin,
                                                             dry_run=dry_run)
        else:
            raise ValueError(f'Command "{cmd}" is not supported')
