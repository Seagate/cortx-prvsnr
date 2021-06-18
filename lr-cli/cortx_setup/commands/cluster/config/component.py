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
#
# Cortx Setup API to execute complete cluster config


import os
import socket
import shutil
from pathlib import Path
from typing import List, Optional

from cortx_setup.config import (
    ALL_MINIONS,
    SOURCE_PATH,
    DEST_PATH
)
from cortx_setup.commands.command import Command
from cortx_setup.commands.pillar_sync import (
    PillarSync
)
from cortx_setup.commands.enclosure.refresh import (
    RefreshEnclosureId
)
from cortx_setup.commands.cluster.encrypt import (
    EncryptSecrets
)
from cortx_setup.commands.cluster.generate import (
    GenerateCluster
)
from cortx_setup.commands.common_utils import (
    get_provisioner_states,
    get_cortx_states
)

from provisioner.commands import (
    bootstrap_provisioner,
    cluster_id,
    create_service_user,
    reset_machine_id,
    confstore_export,
    deploy
)
from provisioner.salt import (
    local_minion_id,
    StatesApplier
)
node_id = local_minion_id()


class ClusterConfigComponent(Command):

    _args = {
        'nodes': {
            'type': str,
            'nargs': '+',
            'optional': False,
            'help': ('List of FQDN of node(s) to be clustered and '
                     'bootstrapped, primary node given first.')
        },
        'source': {
            'type': str,
            'optional': True,
            'default': 'rpm',
            'help': ('Source of build to use for bootstrap. '
                     'e.g: {local|rpm|iso}')
        },
        'dist_type': {
            'type': str,
            'optional': True,
            'default': 'bundle',
            'help': 'Distribution type of build'
        },
        'target_build': {
            'type': str,
            'optional': True,
            'help': 'Target build to bootstrap'
        },
        'ha': {
            'type': bool,
            'optional': True,
            'default': False,
            'help': 'Provide HA option for multi-node setup e.g: --ha'
        },
        'type': {
            'type': str,
            'optional': True,
            'default': None,
            'dest': 'component_group',
            'choices': ['foundation', 'iopath', 'controlpath', 'ha'],
            'help': 'Component group to deploy'
        },
        'iso_cortx': {
            'type': str,
            'optional': True,
            'help': 'iso file path, for iso-source deployment'
        },
        'iso_os': {
            'type': str,
            'optional': True,
            'help': ('iso os path, for iso-source deployment. '
                     'e.g: {/opt/isos/cortx-os-1.0.0-23.iso}')
        },

    }

    def _configure(self, components: List, stages: Optional[List] = None):
        for component in components:
            self.logger.debug(f"Applying components.{component} on nodes")
            try:
                deploy.Deploy()._apply_state(
                    f"components.{component}",
                    stages=stages if stages else None
                )
            except Exception as exc:
                raise exc

    def run(self, **kwargs):
        """
        cortx cluster config command

        Bootstrap system, deploy cortx components

        Execution:
        `cortx_setup cluster config component [nodes_fqdn] --type <state>`

        """
        try:
            print ("kwargs first: " , kwargs)
            self.logger.debug(
              "Checking for basic details in place."
            )
            local_fqdn = socket.gethostname()
            nodes = kwargs['nodes']
            target_build = kwargs['target_build']
            component_group = kwargs['component_group']

            # Parsing nodes
            for idx, node in enumerate(nodes):
                if node == local_fqdn:
                    nodes[idx] = f"srvnode-1:{node}"
                else:
                    nodes[idx] = f"srvnode-{idx+1}:{node}"

            # TODO: Config validation when confstore yaml is used

            # HA validation
            if len(nodes) > 1:
                kwargs['ha'] = True

            # Build validation
            if not target_build:
                target_build = os.environ.get('CORTX_RELEASE_REPO')
                kwargs['target_build'] = target_build
                if not target_build:
                    raise ValueError("'target_build' is mandatory to bootstrap. "
                                     "Please provide valid build URL in command.")

            # ISO files validation
            if kwargs['source'] == 'iso':
                if not (kwargs['iso_cortx'] or kwargs['iso_os']):
                    raise ValueError(
                         "iso single file and iso os file paths are mandatory "
                         "to bootstrap. Please provide valid paths in command.")

            kwargs.pop('component_group')
            self.logger.info(
              "Initial checks done. Follow logs for progress. "
              f"Starting bootstrap process now with args: {kwargs}"
            )
            bootstrap_provisioner.BootstrapProvisioner()._run(**kwargs)

#            # Currently, some changes are needed for this step
#            post_provisioner.PostProvisioner().run(**kwargs)

            self.logger.debug("Cleanup existing storage config")
            if SOURCE_PATH.exists():
                shutil.move(SOURCE_PATH, DEST_PATH)

            self.logger.info(
              "Starting with preparing environment. "
              "Syncing config data now.."
            )
            PillarSync().run()

            self.logger.debug("Refreshing machine id on the system")
            reset_machine_id.ResetMachineId.run()

            self.logger.debug("Generating cluster")
            GenerateCluster().run()

            self.logger.debug("Creating service user")
            create_service_user.CreateServiceUser.run(user="cortxub")

            self.logger.debug("Refreshing enclosure id on the system")
            RefreshEnclosureId().run()

            self.logger.debug("Setting up Cluster ID on the system")
            cluster_id.ClusterId().run()

            self.logger.debug("Encrypting config data")
            EncryptSecrets().run()

            self.logger.debug("Exporting to Confstore")
            confstore_export.ConfStoreExport().run()

            self.logger.info("Bootstrap done. Proceeding to deploy components..")
            self.logger.debug("Deploy system, prereqs and cortx components")

            # Getting provisioner states for deployment
            noncortx_components = get_provisioner_states()
            cortx_components = get_cortx_states()

            if component_group is None:
                for component_group in noncortx_components:
                    self.logger.debug(f"Deploying {component_group} components on nodes")
                    self.logger.debug(f"Deploying {component_group} components on nodes")
                    self._configure(
                        noncortx_components[component_group]
                    )
            elif component_group in cortx_components:
                self.logger.debug(f"Deploying {component_group} components on nodes")
                self._configure(
                    cortx_components[component_group],
                    stages=['config.config', 'config.init_mod']
                )

            return f"Bootstrapped and Deployed node(s): {nodes}"

        except ValueError as exc:
            raise ValueError(
              f"Cluster Config Failed. Reason: {str(exc)}"
            )
