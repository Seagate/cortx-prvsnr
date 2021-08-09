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
from getpass import getpass

from cortx_setup.config import (
    CONFSTORE_CLUSTER_FILE,
    SOURCE_PATH,
    DEST_PATH
)
from cortx_setup.commands.command import Command
from cortx_setup.commands.common_utils import (
    get_cluster_id,
    get_machine_id
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
from cortx_setup.validate import ipv4
from cortx.utils.conf_store import Conf

import provisioner
from provisioner.salt import (
    local_minion_id, cmd_run, StatesApplier
)
from cortx_setup.config import (
    ALL_MINIONS,
    CORTX_ISO_PATH
)

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
                     'e.g: {rpm|iso}')
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
            'help': ('Target build URL '
                    'Required only for remotely hosted Cortx repos.')
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
        },
        'virtual_host': {
            'type': ipv4,
            'default': None,
            'optional': True,
            'help': 'Management vip'
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
            self.provisioner = provisioner

            username = 'nodeadmin'
            password = getpass(prompt=f"Enter {user} user passowrd for srvnode-1:")
            auth_args = {'username': username, 'password': password}
            self.provisioner.auth_init(username, password)

            index = 'cluster_info_index'
            local_minion = None
            local_fqdn = socket.gethostname()
            cluster_args = ['name', 'site_count', 'storageset_count', 'virtual_host']

            # Ref: `nodes` will be removed from this args list.
            # Read more on https://github.com/Seagate/cortx-prvsnr/tree/pre-cortx-1.0/docs/design_updates.md#field-api-design-changes
            nodes = kwargs['nodes']
            target_build = kwargs['target_build']
            source_type = kwargs['source']

            self.logger.debug(
              "Checking for basic details in place."
            )
            # Parsing nodes
            for idx, node in enumerate(nodes):
                if node == local_fqdn:
                    nodes[idx] = f"srvnode-1:{username}@{node}"
                    local_minion = 'srvnode-1'
                else:
                    nodes[idx] = f"srvnode-{idx+1}:{username}@{node}"

            # HA validation
            if len(nodes) > 1:
                kwargs['ha'] = True

            if target_build:
                if not target_build.startswith('http'):
                    raise ValueError(
                        f"Invalid target build provided: {target_build}"
                        " Please provide the valid http or https URL."
                    )
                # target_build and source type iso are mutually exclusive
                if source_type == 'iso':
                    raise TypeError(
                        "The target_build option and the 'source' type "
                        "'iso' are not supported together."
                        " Please run the command with correct options."
                        )
            else:
                # read target build from a file created during factory setup
                tbuild_path = "/opt/seagate/cortx_configs/provisioner_generated/target_build"
                self.logger.info("Fetching the Cortx build source")
                if not os.path.isfile(tbuild_path):
                    raise ValueError(
                        f"The file with Cortx build source"
                        f" doesn't exist: '{tbuild_path}'"
                        f" Please use the --target_build option to"
                        f" provide the correct build URL."
                    )
                with open(tbuild_path, "r") as fh:
                    target_build = fh.readline().strip()

                if not target_build:
                    raise ValueError(
                        "Could not find the Cortx build source."
                        " Please use the --target_build option to"
                        " provide the build url"
                    )

                kwargs['target_build'] = target_build
                # The target build could be a file uri or http url
                # If it's file uri set the source to iso and target_build
                # to None.
                if target_build.startswith('file'):
                    #ISO based deployment
                    kwargs['source'] = 'iso'
                    kwargs['target_build'] = None
                elif not target_build.startswith('http'):
                    raise ValueError(
                        f"Invalid build source found: {target_build}"
                        " Please use --target_build or iso options to"
                        " to provide the correct build source."
                    )

            # ISO files validation
            if kwargs['source'] == 'iso':
                if kwargs['iso_cortx'] and kwargs['iso_os']:
                    ISO_SINGLE_FILE = kwargs['iso_cortx']
                    ISO_OS_FILE = kwargs['iso_os']
                else:
                    self.logger.info("Checking the Cortx ISO files")
                    iso_files = [fn for fn in os.listdir(CORTX_ISO_PATH)
                                    if fn.endswith('.iso')]
                    for name in iso_files:
                        if "single" in name:
                            ISO_SINGLE_FILE = str(CORTX_ISO_PATH) + "/" + name
                        elif "os" in name:
                            ISO_OS_FILE = str(CORTX_ISO_PATH) + "/" + name
                    kwargs['iso_cortx'] = ISO_SINGLE_FILE
                    kwargs['iso_os'] = ISO_OS_FILE

                self.logger.info("Validating the Cortx ISO files")
                if not (os.path.isfile(ISO_SINGLE_FILE)
                        or os.path.isfile(ISO_OS_FILE)):
                    raise ValueError(
                        f"No Cortx ISOs found: "
                        f"{ISO_SINGLE_FILE} & {ISO_OS_FILE}, please"
                        " keep the ISOs at /opt/isos and try again."
                    )

            cluster_dict = {key:kwargs[key]
                           for key in kwargs if key in cluster_args}

            for arg in cluster_args:
                kwargs.pop(arg)

            self.logger.info(
              "Initial checks done. \n"
              "This step will take several minutes.. Follow logs for progress.\n"
              f"Starting bootstrap process now with args: {kwargs}"
            )
            self.provisioner.bootstrap_provisioner(**kwargs)
            if SOURCE_PATH.exists():
                self.logger.debug("Cleanup existing storage config on all nodes")
                cmd_run(
                    f"mv {SOURCE_PATH} {DEST_PATH}", **auth_args
                )
                self.logger.debug("Refreshing config")
                cmd_run(
                    "salt-call saltutil.refresh_pillar", **auth_args
                )

            self.logger.info(
              "Bootstrap Done. Starting with preparing environment. "
              "Syncing config data now.."
            )
            PillarSync().run(**auth_args)

            self.logger.debug("Generating cluster")
            GenerateCluster().run(**auth_args)

            self.logger.debug("Creating service user")
            self.provisioner.create_service_user(user="cortxub")

            node_id = 'srvnode-1'
            self.logger.debug("Setting up Cluster ID on the system")
            self.provisioner.cluster_id(targets=node_id)

            self.logger.debug("Encrypting config data")
            EncryptSecrets().run(**auth_args)

            self.logger.debug("Refreshing enclosure id on the system")
            RefreshEnclosureId().run(**auth_args)

            # NTP workaround.
            # TODO: move this to time.py after encryption issue
            self.logger.debug("Setting time on node with server & timezone")

            StatesApplier.apply(
                [
                    "components.system.chrony.config",
                    "components.system.chrony.stop",
                    "components.system.chrony.start"
                ],
                targets= ALL_MINIONS,
                **auth_args
            )

            machine_id = self.provisioner.grains_get("machine_id")[node_id]["machine_id"]
            enclosure_id = self.provisioner.grains_get("enclosure_id")[node_id]["enclosure_id"]
            if enclosure_id:
                if not machine_id in enclosure_id:   # check if the system is VM or HW
                    self.logger.debug(f"Setting time on enclosure with server & timezone")
                    StatesApplier.apply(
                        [ "components.controller.ntp" ],
                        targets= ALL_MINIONS,
                        **auth_args
                    )
            StatesApplier.apply(
                ['components.system.config.sync_salt'],
                targets=ALL_MINIONS, **auth_args
            )

            self.logger.info("Environment set up! Proceeding to create a cluster..")

            cmd_run(
                f"chown -R {auth_args['username']}:{auth_args['username']} {CONFSTORE_CLUSTER_FILE}",
                **auth_args
            )
            self.load_conf_store(
                index,
                f'json://{CONFSTORE_CLUSTER_FILE}'
            )
            clust_id = self.provisioner.grains_get("cluster_id")[node_id]["cluster_id"]

            for key, value in cluster_dict.items():
                if value and 'virtual_host' not in key:
                    self.logger.debug(
                        f"Updating {key} to {value} in confstore"
                    )
                    self.provisioner.pillar_set(f'cluster/{key}',value)
                    if 'storageset_count' in key:
                        conf_key = f'cluster>{clust_id}>site>storage_set_count'
                    else:
                        conf_key = f'cluster>{clust_id}>{key}'
                    Conf.set(
                        index,
                        conf_key,
                        value
                    )
                if value and 'virtual_host' in key:
                    self.logger.debug(
                        f"Updating virtual_host to {value} in confstore"
                    )
                    self.provisioner.pillar_set('cluster/mgmt_vip',value)
                    Conf.set(
                        index,
                        f'cluster>{clust_id}>network>management>virtual_host',
                        value

                    )
            Conf.save(index)

            self.logger.debug("Exporting to Confstore")
            self.provisioner.confstore_export()

            self.logger.debug("Success: Cluster created")
            return f"Cluster created with node(s): {nodes}"

        except ValueError as exc:
            raise ValueError(
              f"Cluster Create Failed. Reason: {str(exc)}"
            )
