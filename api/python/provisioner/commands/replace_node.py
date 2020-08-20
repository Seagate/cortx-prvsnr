#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging

from .. import (
    config,
    inputs
)
from ..vendor import attr
from ..utils import (
    load_yaml,
    run_subprocess_cmd
)

from .setup_provisioner import (
    Node,
    RunArgsSetupProvisionerBase,
    SetupProvisioner
)


logger = logging.getLogger(__name__)


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
    ha: bool = attr.ib(init=False, default=True)
    profile: bool = attr.ib(
        init=False, default=config.PRVSNR_USER_FACTORY_PROFILE_DIR
    )
    source: str = attr.ib(init=False, default='local')
    prvsnr_verion: str = attr.ib(init=False, default=None)
    local_repo: str = attr.ib(init=False, default=config.PRVSNR_ROOT_DIR)
    target_build: str = attr.ib(init=False, default=None)
    salt_master: str = attr.ib(init=False, default=None)
    update: bool = attr.ib(init=False, default=False)
    rediscover: bool = attr.ib(init=False, default=True)
    field_setup: bool = attr.ib(init=False, default=True)


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
        run_subprocess_cmd(
            [
                'cp', '-r',
                str(config.PRVSNR_FACTORY_PROFILE_DIR),
                str(run_args.profile)
            ]
        )

        paths = config.profile_paths(
            location=run_args.profile.parent,
            setup_name=run_args.profile.name
        )

        logger.info("Adjusting node specs info")
        pillar_all_dir = paths['salt_pillar_dir'] / 'groups/all'
        specs_pillar_path = pillar_all_dir / 'node_specs.sls'
        node_specs = load_yaml(specs_pillar_path)['node_specs']
        nodes = {k: Node(k, **v) for k, v in node_specs.items()}

        if run_args.node_host:
            nodes[run_args.node_id].host = run_args.node_host

        if run_args.node_port:
            nodes[run_args.node_id].port = run_args.node_port

        setup_ctx = super().run(
            nodes=list(nodes.values()), **kwargs
        )

        logger.info("Updating replace node data in pillar")
        setup_ctx.ssh_client.cmd_run(
            (
                '/usr/local/bin/provisioner pillar_set --fpath cluster.sls '
                f'cluster/replace_node/minion_id \'"{run_args.node_id}"\''
            ), targets=run_args.node_id
        )

        logger.info("Setting up replacement_node flag")
        setup_ctx.ssh_client.state_apply(
            'provisioner.post_replacement',
            targets=run_args.node_id
        )

        logger.info("Done")
