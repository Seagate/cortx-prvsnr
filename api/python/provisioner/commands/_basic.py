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

from ..vendor import attr
from .. import inputs, ALL_MINIONS


class RunArgs:
    targets: str = attr.ib(
        default=ALL_MINIONS,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "command's host targets"
            }
        }
    )
    dry_run: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "perform validation only"
            }
        }, default=False
    )
    local: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "use local salt client (salt-call --local)"
            }
        }, default=False
    )


@attr.s(auto_attribs=True)
class RunArgsBase:
    targets: str = RunArgs.targets


class CommandParserFillerMixin:
    _run_args_type = RunArgsBase

    @classmethod
    def _run_args_types(cls):
        ret = cls._run_args_type
        return ret if type(ret) is list else [ret]

    @classmethod
    def fill_parser(cls, parser, parents=None):
        for arg_type in cls._run_args_types():
            inputs.ParserFiller.fill_parser(arg_type, parser)

    @classmethod
    def from_spec(cls):
        return cls()

    @classmethod
    def extract_positional_args(cls, kwargs):
        for arg_type in cls._run_args_types():
            return inputs.ParserFiller.extract_positional_args(
                arg_type, kwargs
            )
