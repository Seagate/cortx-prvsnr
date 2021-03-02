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

from typing import Type, Optional, List
from pathlib import Path
import logging
import argparse

from ..vendor import attr
from .. import (
    inputs,
    config,
    profile
)
from ..node import Node
from .. import utils

from ._basic import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)

default_profile = config.profile_base_dir()


@attr.s(auto_attribs=True)
class SSHProfileGenerator(CommandParserFillerMixin):
    description = (
        "A helper profile generator for salt-ssh. "
        "If '--profile' is specified it would be a profile location. "
        "\nOtherwise if '--name' is specified profile with the name would be "
        f"located inside '{default_profile.parent}' directory. "
        "\nFinally if neither of these options is specified "
        f"default profile would be generated at '{default_profile}'"
    )

    # XXX DRY copy-paste from setup_provisioner.py
    nodes: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "cluster node specification, "
                    "format: id:[user@]hostname[:port]"
                ),
                'nargs': '+'
            }
        },
        converter=(
            lambda specs: [
                (s if isinstance(s, Node) else Node.from_spec(s))
                for s in specs
            ]
        )
    )
    name: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "A name to assign to the setup profile "
                    f"generated inside {default_profile.parent} "
                    "(ignored if '--profile' option is specified)."
                ),
            }
        },
        default=None
    )
    profile: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "the path to the setup profile directory, "
                    "by default auto-generated inside current directory,  "
                    "if specified '--name' option is ignored"
                )
            }
        },
        default=None,
        converter=(lambda v: Path(str(v)) if v else v)
    )
    # XXX validation
    add_file_roots: Optional[List] = attr.ib(
        default=attr.Factory(list),
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "additional file roots",
                'metavar': 'PATH',
                'nargs': '*'
            }
        }
    )
    add_pillar_roots: Optional[List] = attr.ib(
        default=attr.Factory(list),
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "additional pillar roots",
                'metavar': 'PATH',
                'nargs': '*'
            }
        }
    )
    ssh_key: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "ssh key",
                'metavar': 'PATH'
            }
        },
        default=None,
        converter=(lambda v: Path(str(v)) if v else v),
        validator=utils.validator_path_exists
    )
    cleanup: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "cleanup existing profile"
                )
            }
        },
        default=False,
    )

    def __attrs_post_init__(self):
        if not self.profile:
            if self.name:
                self.profile = default_profile.parent / self.name
            else:
                self.profile = default_profile

        self.add_file_roots = [Path(p) for p in self.add_file_roots]
        self.add_pillar_roots = [Path(p) for p in self.add_pillar_roots]

    def run(self):
        paths = config.profile_paths(
            config.profile_base_dir(
                location=self.profile.parent,
                setup_name=self.profile.name
            )
        )

        profile.setup(
            paths,
            clean=self.cleanup,
            add_file_roots=self.add_file_roots,
            add_pillar_roots=self.add_pillar_roots
        )

        ssh_key = self.ssh_key
        if not ssh_key:
            ssh_key = paths['setup_key_file']

            if not ssh_key.exists():
                logger.warning(
                    "SSH key in roster would be set to a default path"
                    f" {ssh_key} which doesn't exist yet"
                )

        roster = {
            node.minion_id: {
                'host': node.host,
                'user': node.user,
                'port': node.port,
                'priv': str(ssh_key)
            } for node in self.nodes
        }
        utils.dump_yaml(paths['salt_roster_file'], roster)


@attr.s(auto_attribs=True)
class HelperGenerator(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = None

    helpers = {
        'ssh_profile': SSHProfileGenerator
    }

    @classmethod
    def fill_parser(cls, parser, parents=None):
        if parents is None:
            parents = []

        subparsers = parser.add_subparsers(
            dest='helper',
            title='Various helpers',
            description='valid helpers'
        )

        for helper_name, helper_t in cls.helpers.items():
            subparser = subparsers.add_parser(
                helper_name, description=helper_t.description,
                help=f"{helper_name} helper help", parents=parents,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
            inputs.ParserFiller.fill_parser(helper_t, subparser)

    # XXX DRY copy-paste from SaltClient command
    @classmethod
    def extract_positional_args(cls, kwargs):
        helper_t = cls.helpers[kwargs.pop('helper')]
        _args = [helper_t]

        args, kwargs = super().extract_positional_args(kwargs)
        _args.extend(args)

        args, kwargs = inputs.ParserFiller.extract_positional_args(
            helper_t, kwargs
        )
        _args.extend(args)

        return _args, kwargs

    @staticmethod
    def run(helper_t, *args, **kwargs):
        helper_kwargs = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(helper_t)
        }

        helper = helper_t(*args, **helper_kwargs)

        return helper.run(**kwargs)
