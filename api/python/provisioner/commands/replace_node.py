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

from .. import (
    config,
    inputs,
    errors
)
from ..vendor import attr
from ..utils import (
    load_yaml,
    run_subprocess_cmd
)
from ..pillar import PillarUpdater
from ..salt import local_minion_id

from .setup_provisioner import (
    Node,
    RunArgsSetupProvisionerBase,
    SetupProvisioner
)


logger = logging.getLogger(__name__)

add_pillar_merge_prefix = PillarUpdater.add_merge_prefix


@attr.s(auto_attribs=True)
class RunArgsReplaceNode(RunArgsSetupProvisionerBase):
    node_id: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "new node minion id",
                'metavar': 'ID'
            }
        },
        default='srvnode-2'
    )
    node_host: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "new node host, by default the same is used",
                'metavar': 'HOST'
            }
        },
        default=None
    )
    node_port: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "new node port, by default the same is used",
                'metavar': 'PORT'
            }
        },
        default=None
    )

    name: str = attr.ib(init=False, default=None)
    # not needed since pillar is already set
    config_path: str = attr.ib(init=False, default=None)
    profile: bool = attr.ib(
        init=False, default=config.PRVSNR_USER_FACTORY_PROFILE_DIR
    )
    # not needed: would beset as for initial setup
    source: str = attr.ib(init=False, default=None)
    prvsnr_version: str = attr.ib(init=False, default=None)
    iso_os: str = attr.ib(init=False, default=None)
    iso_cortx: str = attr.ib(init=False, default=None)
    iso_cortx_deps: str = attr.ib(init=False, default=None)
    url_cortx_deps: str = attr.ib(init=False, default=None)
    dist_type: str = attr.ib(init=False, default=None)
    target_build: str = attr.ib(init=False, default=None)
    salt_master: str = attr.ib(init=False, default=None)
    # in case source is local default production location
    # would b treated as a repo
    local_repo: str = attr.ib(init=False, default=config.PRVSNR_ROOT_DIR)
    # retain factory profile
    update: bool = attr.ib(init=False, default=False)
    # rediscover since new node
    rediscover: bool = attr.ib(init=False, default=True)
    # it is a field setup actually
    field_setup: bool = attr.ib(init=False, default=True)
    # replacement is considered only for HA mode
    ha: bool = attr.ib(init=False, default=True)


@attr.s(auto_attribs=True)
class ReplaceNode(SetupProvisioner):
    _run_args_type = RunArgsReplaceNode

    def run(self, **kwargs):
        run_args = RunArgsReplaceNode(**kwargs)
        kwargs = attr.asdict(run_args)
        kwargs.pop('node_id')
        kwargs.pop('node_host')
        kwargs.pop('node_port')

        logger.info("Preparing user profile")
        run_subprocess_cmd(['rm', '-rf',  str(run_args.profile)])
        run_args.profile.parent.mkdir(parents=True, exist_ok=True)

        # On some systems 'cp -i' alias, breaks the next step.
        # This fix addresses it
        ret_val = run_subprocess_cmd(['alias'])
        if "cp -i" in ret_val.stdout:
            run_subprocess_cmd(['unalias', 'cp'])

        factory_profile = config.PRVSNR_FACTORY_PROFILE_DIR
        if not factory_profile.is_dir():
            factory_profile = (
                config.GLUSTERFS_VOLUME_PRVSNR_DATA / 'factory_profile'
            )

        if not factory_profile.is_dir():
            raise errors.ProvisionerRuntimeError(
                'factory profile directory is not found'
            )

        run_subprocess_cmd(
            ['cp', '-fr', str(factory_profile), str(run_args.profile)]
        )

        paths = config.profile_paths(
            config.profile_base_dir(
                location=run_args.profile.parent,
                setup_name=run_args.profile.name
            )
        )

        pillar_all_dir = paths['salt_pillar_dir'] / 'groups/all'

        logger.info("Loading initial setup parameters")
        setup_pillar_path = add_pillar_merge_prefix(
            pillar_all_dir / 'factory_setup.sls'
        )
        setup_args = load_yaml(setup_pillar_path)['factory_setup']

        # set some parameters as for initial setup
        for _attr in (
            'source',
            'prvsnr_version',
            'iso_os',
            'iso_cortx',
            'iso_cortx_deps',
            'url_cortx_deps',  # TODO IMPROVE may rely on profile data
            'dist_type',
            'target_build',
            'salt_master',
            'ha'
        ):
            kwargs[_attr] = setup_args[_attr]

        # FIXME EOS-13803
        kwargs.pop('url_cortx_deps', None)

        logger.info("Adjusting node specs info")
        specs_pillar_path = add_pillar_merge_prefix(
            pillar_all_dir / 'node_specs.sls'
        )
        node_specs = load_yaml(specs_pillar_path)['node_specs']
        nodes = {k: Node(k, **v) for k, v in node_specs.items()}

        if run_args.node_host:
            nodes[run_args.node_id].host = run_args.node_host

        if run_args.node_port:
            nodes[run_args.node_id].port = run_args.node_port

        # make the current node primary (the first in the list)
        # assumption:
        #   salt's local client is available since the command
        #   should be run on a healthy node
        primary_id = local_minion_id()
        setup_ctx = super()._run(
            nodes=[nodes.pop(primary_id)] + list(nodes.values()),
            **kwargs
        )

        logger.info("Updating replace node data in pillar")
        setup_ctx.ssh_client.cmd_run(
            (
                'provisioner pillar_set --fpath cluster.sls '
                f'cluster/replace_node/minion_id \'"{run_args.node_id}"\''
            ), targets=run_args.node_id
        )

        logger.info("Setting up replacement_node flag")
        setup_ctx.ssh_client.state_apply(
            'provisioner.post_replacement',
            targets=run_args.node_id
        )

        logger.info("Done")
