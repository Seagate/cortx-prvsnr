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
import logging
import argparse

from ..vendor import attr
from .. import (
    inputs
)
from ..cli_parser import KeyValueListAction

from ..salt_api import (
    SaltLocalClient,
    SaltRunnerClient,
    SaltCallerClient,
    SaltLocalCallerClient,
    SaltSSHClient
)

from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsSaltFun:
    fun: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "salt function to run"
                )
            }
        }
    )
    fun_args: str = attr.ib(
        kw_only=True,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "salt fun key-value arguments"
                ),
                'metavar': 'ARG',
                'nargs': '+',
            }
        },
        default=None
    )
    fun_kwargs: str = attr.ib(
        kw_only=True,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "salt fun keyword arguments"
                ),
                'metavar': 'KEY=VALUE',
                'nargs': '+',
                'action': KeyValueListAction
            }
        },
        default=None
    )
    kwargs: str = attr.ib(
        kw_only=True,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "salt client keyword arguments"
                ),
                'metavar': 'KEY=VALUE',
                'nargs': '+',
                'action': KeyValueListAction
            }
        },
        default=None
    )
    secure: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "mask secrets in logs"
                )
            }
        },
        default=False
    )


# TODO DOC example how to organize subcommands
@attr.s(auto_attribs=True)
class SaltClient(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSaltFun

    clients = {
        'salt': SaltLocalClient,
        'runner': SaltRunnerClient,
        'caller': SaltCallerClient,
        'local': SaltLocalCallerClient,
        'ssh': SaltSSHClient
    }

    @classmethod
    def fill_parser(cls, parser, parents=None):
        if parents is None:
            parents = []

        parser_common = argparse.ArgumentParser(add_help=False)
        super().fill_parser(parser_common)

        parents.append(parser_common)

        subparsers = parser.add_subparsers(
            dest='client',
            title='clients',
            description='valid clients'
        )

        for cl_name, cl_t in cls.clients.items():
            subparser = subparsers.add_parser(
                cl_name, description='{} configuration'.format(cl_name),
                help='{} client help'.format(cl_name), parents=parents,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
            inputs.ParserFiller.fill_parser(cl_t, subparser)

    @classmethod
    def extract_positional_args(cls, kwargs):
        client_t = cls.clients[kwargs.pop('client')]
        _args = [client_t]

        args, kwargs = super().extract_positional_args(kwargs)
        _args.extend(args)

        args, kwargs = inputs.ParserFiller.extract_positional_args(
            client_t, kwargs
        )
        _args.extend(args)

        return _args, kwargs

    @staticmethod
    def run(client_t, fun, *args, **kwargs):
        client_kwargs = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(client_t)
        }

        run_args = RunArgsSaltFun(fun, **{
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(RunArgsSaltFun)
        })

        client = client_t(*args, **client_kwargs)

        return client.run(
            run_args.fun,
            run_args.fun_args,
            run_args.fun_kwargs,
            run_args.secure,
            **(run_args.kwargs or {})
        )
