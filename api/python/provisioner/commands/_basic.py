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

from typing import Optional, Union, Type

from ..vendor import attr
from .. import inputs, config
from ..utils import validator__subclass_of
from ..paths import PillarPath, FileRootPath

from ..salt_api import (
    SaltLocalClient,
    SaltRunnerClient,
    SaltCallerClient,
    SaltLocalCallerClient,
    SaltSSHClient
)
from ..salt_api.base import SaltClientBaseParams


class RunArgs:
    targets: str = attr.ib(
        default=config.ALL_MINIONS,
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
    runner_minion_id: Optional[str] = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "remote target to run a command on"
            }
        }
    )


def converter__str_to_salt_client_t(client: str):
    clients = {
        'salt': SaltLocalClient,
        'runner': SaltRunnerClient,
        'caller': SaltCallerClient,
        'local': SaltLocalCallerClient,
        'ssh': SaltSSHClient
    }
    return clients[client]


# XXX duplicates salt clients args definitions
# XXX duplicates SSHProfile from helper.py
class RunArgsSaltClientParams:
    salt_client_type: Optional[
        Union[str, Type[SaltLocalClient], Type[SaltSSHClient]]
    ] = attr.ib(
        default='salt',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "salt client type"
            },
            'choices': ['salt', 'ssh'],
            'metavar': 'STR'
        },
        converter=converter__str_to_salt_client_t,
        validator=validator__subclass_of((SaltLocalClient, SaltSSHClient))
    )
    salt_c_path: str = attr.ib(
        default=config.SALT_MASTER_CONFIG_DEFAULT,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config path"
            }
        }
    )
    salt_ssh_roster: str = attr.ib(
        default=config.SALT_ROSTER_DEFAULT,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "path to roster file"
            }
        }
    )
    salt_ssh_profile: str = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "path to ssh profile, if specified"
                    " paths to roster, roots and configuration files"
                    " would be set automatically"
                )
            }
        }
    )
    salt_ssh_profile_name: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "A name of the setup profile "
                    f"considered inside {config.profile_base_dir().parent} "
                    "(ignored if '--salt-ssh-profile' option is specified)."
                ),
            }
        },
        default=None
    )


@attr.s(auto_attribs=True)
class RunArgsBase:
    targets: str = RunArgs.targets
    runner_minion_id: str = RunArgs.runner_minion_id


@attr.s(auto_attribs=True)
class RunArgsSaltClient:
    salt_client_type: Optional[
        Union[str, Type[SaltLocalClient], Type[SaltSSHClient]]
    ] = RunArgsSaltClientParams.salt_client_type
    salt_c_path: str = RunArgsSaltClientParams.salt_c_path
    salt_ssh_roster: str = RunArgsSaltClientParams.salt_ssh_roster
    salt_ssh_profile: str = RunArgsSaltClientParams.salt_ssh_profile
    salt_ssh_profile_name: str = (
        RunArgsSaltClientParams.salt_ssh_profile_name
    )
    fileroot_path: Union[FileRootPath, str] = (
        SaltClientBaseParams.fileroot_path
    )
    pillar_path: Union[PillarPath, str] = SaltClientBaseParams.pillar_path

    client: str = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        kwargs = dict(
            c_path=self.salt_c_path,
            fileroot_path=self.fileroot_path,
            pillar_path=self.pillar_path
        )

        if issubclass(self.salt_client_type, SaltSSHClient):
            if self.salt_ssh_profile_name and not self.salt_ssh_profile:
                self.salt_ssh_profile = (
                    config.profile_base_dir().parent
                    / self.salt_ssh_profile_name
                )

            # XXX EOS-17600 re_config always True here
            kwargs.update(dict(
                profile=self.salt_ssh_profile,
                roster_file=self.salt_ssh_roster,
                re_config=True
            ))

        self.client = self.salt_client_type(**kwargs)  # pylint: disable=not-callable


@attr.s(auto_attribs=True)
class ProvisionerCommand:
    """Base class for provisioner commands."""


# XXX rethink class hirarchy, it's no more mixin actually
class CommandParserFillerMixin:
    _run_args_type = RunArgsBase

    @classmethod
    def _run_args_types(cls):
        ret = cls._run_args_type
        return ret if isinstance(ret, list) else [ret] if ret else []

    @classmethod
    def fill_parser(cls, parser, parents=None):
        for arg_type in cls._run_args_types():
            inputs.ParserFiller.fill_parser(arg_type, parser)

    @classmethod
    def from_spec(cls):
        return cls()

    @classmethod
    def extract_positional_args(cls, kwargs):
        res = []
        for arg_type in cls._run_args_types():
            _args, kwargs = inputs.ParserFiller.extract_positional_args(
                arg_type, kwargs
            )
            res.extend(_args)
        return res, kwargs
