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
from pathlib import Path
from cortx_setup.commands.command import Command
from cortx_setup.commands.enclosure.refresh import (
    RefreshEnclosureId
)
from cortx_setup.commands.cluster.encrypt import (
    EncryptPillar
)
from cortx_setup.config import (
    ALL_MINIONS,
    CONFIG_PATH
)

from provisioner.commands import (
    bootstrap_provisioner,
    cluster_id,
    create_service_user,
    reset_machine_id,
    confstore_export
)
from provisioner.salt import StatesApplier


class CortxClusterConfig(Command):

    # TODO: changes needed in API logic to finalise args
    _args = {
        'nodes': {
            'type': str,
            'nargs': '+',
            'optional': False,
            'help': ('List of FQDN of node(s) to be clustered and '
                     'bootstrapped, primary node given first.')
        },
        'config_path': {
            'type': str,
            'optional': True,
            'default': CONFIG_PATH,
            'help': 'Config file path for bootstrap.'
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

    def run(self, **kwargs):

        try:
            self.logger.debug(
              "Checking for basic details in place."
            )
            local_fqdn = socket.gethostname()
            nodes = kwargs['nodes']
            config_path = Path(kwargs['config_path'])
            target_build = kwargs['target_build']

            # Parsing nodes
            for idx, node in enumerate(nodes):
                if node == local_fqdn:
                    nodes[idx] = f"srvnode-1:{node}"
                else:
                    nodes[idx] = f"srvnode-{idx+1}:{node}"

            # Config validation
            if not (CONFIG_PATH.exists() or config_path.exists()):
                raise ValueError(f"'{config_path}' not found. "
                                 "Please provide valid config path in command.")

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

            self.logger.debug(
              "Initial checks done. "
              f"Starting bootstrap process now with args: {kwargs}"
            )
            bootstrap_provisioner.BootstrapProvisioner()._run(**kwargs)

#            # Currently, some changes are needed for this step
#            post_provisioner.PostProvisioner().run(**kwargs)

            self.logger.debug(
              "Starting with preparing environment. "
              "Creating service user now."
            )
            create_service_user.CreateServiceUser.run(user="cortxub")

            self.logger.debug("Refreshing machine id on the system")
            reset_machine_id.ResetMachineId.run()

            self.logger.debug("Refreshing enclosure id on the system")
            RefreshEnclosureId().run()

            self.logger.debug("Generating cluster")
            StatesApplier.apply(
                  ["components.provisioner.config"], targets=ALL_MINIONS
            )

            self.logger.debug("Setting up Cluster ID on the system")
            cluster_id.ClusterId().run()

            self.logger.debug("Encrypting config data")
            EncryptPillar().run()

            self.logger.debug("Exporting to Confstore")
            confstore_export.ConfStoreExport().run()

            return f"Bootstrap done for node(s): '{nodes}'"

        except ValueError as exc:
            raise ValueError(
              f"Cluster Config Failed. Reason: {str(exc)}"
            )
