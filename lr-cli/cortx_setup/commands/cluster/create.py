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
# Cortx Setup API to bootstrap and create a logical cluster


import os
import socket
import shutil

from cortx_setup.config import (
    CONFSTORE_CLUSTER_FILE,
    SOURCE_PATH,
    DEST_PATH
)
from cortx_setup.commands.command import Command
from cortx_setup.commands.common_utils import (
    get_cluster_id
)
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
from cortx_setup.commands.node.prepare.time import (
    NodePrepareTime
)
from cortx_setup.commands.common_utils import get_machine_id

from cortx.utils.conf_store import Conf

from provisioner.commands import (
    PillarSet,
    bootstrap_provisioner,
    confstore_export,
    cluster_id,
    create_service_user,
    reset_machine_id
)
from provisioner.salt import (
    local_minion_id,
)
from provisioner.api import grains_get

class ClusterCreate(Command):

    _args = {
        'name': {
            'type': str,
            'optional': True
        },
        'site_count': {
            'type': int,
            'optional': True
        },
        'storageset_count': {
            'type': int,
            'optional': True
        },
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
        }
    }


    def run(self, **kwargs):
        """
        cortx cluster config command

        Bootstrap system, deploy cortx components

        Execution:
        `cortx_setup cluster create [nodes_fqdn] --name <cluster_name>`

        """
        try:
            index = 'node_info_index'
            local_fqdn = socket.gethostname()
            cluster_args = ['name', 'site_count', 'storageset_count']

            # Ref: `nodes` will be removed from this args list. Read more on https://github.com/Seagate/cortx-prvsnr/tree/pre-cortx-1.0/docs/design_updates.md#field-api-design-changes
            nodes = kwargs['nodes']
            target_build = kwargs['target_build']

            self.logger.debug(
              "Checking for basic details in place."
            )
            # Parsing nodes
            for idx, node in enumerate(nodes):
                if node == local_fqdn:
                    nodes[idx] = f"srvnode-1:{node}"
                else:
                    nodes[idx] = f"srvnode-{idx+1}:{node}"

            # TODO: Config validation only when confstore yaml is used

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

            cluster_dict = {key:kwargs[key]
                           for key in kwargs if key in cluster_args}

            for arg in cluster_args:
                kwargs.pop(arg)

            self.logger.info(
              "Initial checks done. \n"
              "This step will take several minutes.. Follow logs for progress.\n"
              f"Starting bootstrap process now with args: {kwargs}"
            )
            bootstrap_provisioner.BootstrapProvisioner()._run(**kwargs)

            if SOURCE_PATH.exists():
                self.logger.debug("Cleanup existing storage config")
                shutil.move(SOURCE_PATH, DEST_PATH)

            self.logger.info(
              "Starting with preparing environment. "
              "Syncing config data now.."
            )
            PillarSync().run()

            self.logger.debug("Generating cluster")
            GenerateCluster().run()

            self.logger.debug("Creating service user")
            create_service_user.CreateServiceUser.run(user="cortxub")

            self.logger.debug("Setting up Cluster ID on the system")
            cluster_id.ClusterId().run()

            self.logger.debug("Encrypting config data")
            EncryptSecrets().run()

            self.logger.debug("Refreshing enclosure id on the system")
            RefreshEnclosureId().run()

            #NTP workaround for now(need to move this to time.py after encryption issue)
            self.logger.debug(f"Setting time on node with server & timezone")
            node_id = local_minion_id()
            NodePrepareTime().set_server_time()
            machine_id = get_machine_id(node_id)
            enclosure_id = grains_get("enclosure_id")[node_id]["enclosure_id"]
            if enclosure_id:
                if not machine_id in enclosure_id:   # check if the system is VM or HW
                    self.logger.debug(f"Setting time on enclosure with server & timezone")
                    NodePrepareTime().set_enclosure_time()


            self.logger.debug("Exporting to Confstore")
            confstore_export.ConfStoreExport().run()

            self.logger.info("Environment set up! Proceeding to create a cluster..")

            Conf.load(
                index,
                f'json://{CONFSTORE_CLUSTER_FILE}'
            )
            clust_id = get_cluster_id()
            for key, value in cluster_dict.items():
                if value:
                    self.logger.debug(
                        f"Updating {key} to {value} in confstore"
                    )
                    PillarSet().run(
                        f'cluster/{key}',
                        value,
                        local=True
                    )
                    Conf.set(
                        index,
                        f'cluster>{clust_id}>{key}',
                        value
                    )
            Conf.save(index)
            self.logger.debug("Success: Cluster created")
            return f"Cluster created with node(s): {nodes}"

        except ValueError as exc:
            raise ValueError(
              f"Cluster Create Failed. Reason: {str(exc)}"
            )
