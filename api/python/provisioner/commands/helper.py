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
from ..ssh import keygen

from ._basic import (
    CommandParserFillerMixin
)
from ..salt_api import SaltSSHClient


logger = logging.getLogger(__name__)

default_profile = config.profile_base_dir()


class RunArgsHelpersParams:
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
    profile_name: str = attr.ib(
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
    ssh_key: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "ssh key",
                'metavar': 'PATH'
            }
        },
        default=None,
        converter=utils.converter_path_resolved,
        validator=utils.validator_path_exists
    )
    bootstrap_key: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "bootstrap key for initial access only",
                'metavar': 'PATH'
            }
        },
        default=None,
        converter=utils.converter_path_resolved,
        validator=utils.validator_path_exists
    )


@attr.s(auto_attribs=True)
class SSHProfile:

    profile_name: str = RunArgsHelpersParams.profile_name
    profile: str = RunArgsHelpersParams.profile

    def __attrs_post_init__(self):
        if not self.profile:
            if self.profile_name:
                self.profile = default_profile.parent / self.profile_name
            else:
                self.profile = default_profile


@attr.s(auto_attribs=True)
class SSHProfileGenerator(SSHProfile, CommandParserFillerMixin):
    description = (
        "A helper profile generator for salt-ssh."
        "  If '--profile' is specified it would be a profile location."
        " Otherwise if '--name' is specified profile with the name would be"
        f" located inside '{default_profile.parent}' directory."
        " Finally if neither of these options is specified"
        f" default profile would be generated at '{default_profile}'"
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
        super().__attrs_post_init__()

        self.add_file_roots = [Path(p) for p in self.add_file_roots]
        self.add_pillar_roots = [Path(p) for p in self.add_pillar_roots]

    def run(self):
        paths = config.profile_paths(
            config.profile_base_dir(profile=self.profile)
        )

        logger.debug(f"Generating profile at '{self.profile}'")
        profile.setup(
            paths,
            clean=self.cleanup,
            add_file_roots=self.add_file_roots,
            add_pillar_roots=self.add_pillar_roots
        )

        logger.info(
            f"Generated profile location is '{self.profile}'."
        )


@attr.s(auto_attribs=True)
class EnsureNodesReady(SSHProfile, CommandParserFillerMixin):
    description = (
        "Ensures the nodes are accessible and ready to accept "
        " provisioner commands."
        " If '--profile' is specified it would be used as a profile location."
        " Otherwise if '--name' is specified profile with that name"
        f" will be considered inside '{default_profile.parent}' directory."
        " Finally if neither of these options is specified"
        f" default profile at '{default_profile}' would be used."
        "If '--ssh-key' is specified then a public key at the same location"
        " is considered."
    )

    nodes: str = RunArgsHelpersParams.nodes
    profile_name: str = RunArgsHelpersParams.profile_name
    profile: str = RunArgsHelpersParams.profile
    ssh_key: str = RunArgsHelpersParams.ssh_key
    bootstrap_key: str = RunArgsHelpersParams.bootstrap_key

    regenerate_key: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Re-generate an access key if exists"
            }
        },
        default=False
    )

    def run(self):
        paths = config.profile_paths(
            config.profile_base_dir(profile=self.profile)
        )
        bootstrap_roster = paths['salt_bootstrap_roster_file']

        ssh_key = self.ssh_key
        if not ssh_key:
            ssh_key = paths['setup_key_file']

            if self.regenerate_key or not ssh_key.exists():
                logger.debug(f"Generating access key as '{ssh_key}'")
                keygen(ssh_key)

        logger.debug(f"Generating roster as '{paths['salt_roster_file']}'")
        SaltSSHClient.build_roster(
            self.nodes, ssh_key, paths['salt_roster_file']
        )

        ssh_client = SaltSSHClient(profile=self.profile)

        if self.bootstrap_key:
            logger.debug(
                f"Generating bootstrap roster as '{bootstrap_roster}'"
            )
            ssh_client.build_roster(
                self.nodes, self.bootstrap_key, bootstrap_roster
            )
        elif bootstrap_roster.exists():
            logger.warning(
                f"Existent bootstrap roster '{bootstrap_roster}' will be used"
            )

        # if self.bootstrap_key:
        #     ssh_client.add_file_roots([self.bootstrap_key.parent])

        for node in ssh_client.roster_targets():
            logger.info(
                f"Ensuring '{node}' is ready to accept commands"
            )
            ssh_client.ensure_ready(
                [node],
                bootstrap_roster_file=(
                    bootstrap_roster if bootstrap_roster.exists() else None
                )
            )


@attr.s(auto_attribs=True)
class Helper(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = None

    helpers = {
        'generate-profile': SSHProfileGenerator,
        'ensure-nodes-ready': EnsureNodesReady
    }

    @classmethod
    def fill_parser(cls, parser, parents=None):
        if parents is None:
            parents = []

        subparsers = parser.add_subparsers(
            dest='helper',
            title='Various helpers',
            description='valid helpers',
            # requried=True # ( sad, but python 3.6 doesn't have that
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
