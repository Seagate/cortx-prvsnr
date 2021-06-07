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


from cortx_setup.commands.command import Command
# from ..common_utils import call_provisioner_cmd

from cortx_setup.commands.enclosure.refresh import (
    RefreshEnclosureId
)
from cortx_setup.commands.cluster.encrypt import (
    EncryptPillar
)

from cortx_setup.config import (
    CONFSTORE_CLUSTER_FILE,
    ALL_MINIONS
)
from cortx.utils.conf_store import Conf

from provisioner.commands import (
    bootstrap_provisioner,
    post_provisioner,
    cluster_id,
    create_service_user,
    reset_machine_id,
    confstore_export
)
from provisioner.salt import (
    cmd_run,
    StateFunExecuter
)


class ClusterConfig(Command):

    # TODO: test and finalise args
    _args = {
        'node': {
            'type': str,
            'nargs': '+',
            'optional': True,
            'help': 'List of node(s) to be clustered and bootstrapped'
        },
        'source': {
            'type': str,
            'optional': True,
            'help': 'Source of build to use for bootstrap'
        },
        'dist_type': {
            'type': str,
            'optional': True,
            'help': 'Distribution type of build'
        },
        'target_build': {
            'type': str,
            'optional': True,
            'help': 'Target build to bootstrap'
        }

    }

    def run(self, node=None, source=None,
            dist_type=None, target_build=None):

        try:
            index = 'bootstrap_index'

            config_path = CONFSTORE_CLUSTER_FILE
            loaded_config = Conf.load(
                index,
                f'json://{CONFSTORE_CLUSTER_FILE}'
            )

            self.logger.debug(
              "Starting bootstrap process for node(s): '{node}' now.."
            )
            # Common method needed?
            # bootstrap = call_provisioner_cmd(bootstrap_provisioner, nodes)

            bootstrap_provisioner.BootstrapProvisioner._run(
                nodes, source, dist_type, config_path, target_build
            )

            self.logger.debug(
              "Bootstrap done.. Starting with prepare environment now.."
            )
            post_provisioner.PostProvisioner.run(
                nodes, source, dist_type, config_path, target_build
            )

            self.logger.debug(
              "Post-bootstrap steps done. Creating service user now.."
            )
            # get `user` from confstore data
            create_service_user.CreateServiceUser.run(user)

            self.logger.debug("Refreshing machine id on the system")
            reset_machine_id.ResetMachineId.run("force")

            self.logger.debug("Refreshing enclosure id on the system")
            RefreshEnclosureId.run(self)

            self.logger.debug("Setting up Cluster ID on the system")
            cluster_id.ClusterId.run()

            self.logger.debug("Encrypting config data")
            EncryptPillar.run(self)

            self.logger.debug("Exporting to Confstore")
            confstore_export.ConfStoreExport.run()

            return f"Bootstrap done for node(s): '{node}'"

        except ValueError as exc:
            raise ValueError(
              f"Cluster Config Failed. Reason: {str(exc)}"
            )
