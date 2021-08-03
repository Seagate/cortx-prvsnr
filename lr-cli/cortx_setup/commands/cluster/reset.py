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

from cortx_setup.commands.command import Command
from cortx_setup.commands.common_utils import (
    get_reset_states,
    get_pillar_data
)
from cortx_setup.config import (
    BACKUP_FACTORY_FOLDER,
    BACKUP_FILE_DICT,
    CLEANUP_FILE_LIST
)
from provisioner.config import ALL_MINIONS
from provisioner.commands import (
    deploy
)
from provisioner.salt import (
    StatesApplier,
    cmd_run,
    local_minion_id
)
from provisioner.vendor import attr
from provisioner.commands.destroy import (
    SetupCtx,
    RunArgsDestroy,
    DestroyNode
)
from provisioner.commands.generate_roster import (
    GenerateRoster,
    RunArgsGenerateRosterAttrs
)

salt_basic_config_script = '/opt/seagate/cortx/provisioner/srv/components/provisioner/scripts/salt.sh'

class ClusterResetNode(Command):
    _args = {
        'type': {
            'type': str,
            'optional': True,
            'help': 'reset all/data'
        }
    }

    def _create_saltssh_client(self):
        """
        Creates salt roster file and salt-ssh connection
        """
        salt_config_master = '/etc/salt/master'
        roster_file = f'{BACKUP_FACTORY_FOLDER}/roster'

        roster_params = attr.asdict(RunArgsGenerateRosterAttrs())
        roster_params['roster_path'] = roster_file
        GenerateRoster().run(**roster_params)

        self.ssh_client = DestroyNode._create_ssh_client(salt_config_master, roster_file)

    def _apply_states(self, states: list, targets=None):
        try:
            for state in states:
                self.logger.debug(f"Running {state}")
                self.ssh_client.state_apply(
                    f"components.{state}",
                    targets=targets,
                    tgt_type='pcre'
                )
        except Exception as exc:
            self.logger.error(
                f"Failed {state} on {targets}\n"
                f"Error: {str(exc)}"
            )
            raise

    def _run_cmd(self, cmds : list, targets=None):
        for cmd in cmds:
            self.logger.info(f"Running command {cmd} ")
            try:
                self.ssh_client.cmd_run(
                    f"{cmd}",
                    targets=targets,
                    tgt_type='pcre'
                )
            except Exception as exc:
                self.logger.error(
                    f"Failed cmd {cmd} on {targets}\n"
                    f"Error: {str(exc)}"
                )
                raise

    # deploy the specific component states wrt to stages like reset,cleanup
    def _destroy(self, components: dict, stage: list = None):
        for component in components:
            states = components[component]
            for state in states:
                try:
                    self.logger.debug(
                        f"Running {state} for ALL_MINIONS"
                    )
                    deploy.Deploy()._apply_state(
                        f'components.{state}', targets= ALL_MINIONS, stages=stage
                    )
                except Exception as ex:
                    raise ex

    @staticmethod
    def cluster_stop():
        res = cmd_run('cortx cluster stop --all', targets=local_minion_id())
        return next(iter(res.values()))

    @staticmethod
    def cluster_start():
        res = cmd_run('cortx cluster start', targets=local_minion_id())
        return next(iter(res.values()))

    def run(self, **kwargs):
        reset_type= kwargs.get('type')
        cortx_components = get_reset_states()
        self.node_list = get_pillar_data('cluster/node_list')

        self.logger.info(f"Reset to be done for type is {reset_type}")

        self.logger.info("Stopping the cluster")
        self.cluster_stop()

        self.logger.info("Calling reset for cortx components")

        if reset_type == 'data':
            self.logger.info("Calling reset data for cortx components")
            self._destroy(cortx_components, stage=["teardown.reset"])

            self.logger.info("Cleaning up provisioner logs and metadata")
            StatesApplier.apply(
                ["components.provisioner.teardown.reset"],
                targets=ALL_MINIONS
            )

            self.logger.info("starting the cluster")
            self.cluster_start()
            self.logger.info("Done")

        elif reset_type == 'all':
            self.logger.info("Performing post Factory reset for Cortx components.")
            self._destroy(cortx_components, stage=["teardown.reset", "teardown.cleanup"])

            self.logger.debug("Preparing Reset for Provisioner commands")
            
            provisioner_components = [
                "provisioner.salt.stop",
                "system.storage.glusterfs.teardown.volume_remove",
                "system.storage.glusterfs.teardown.stop",
                "system.storage.glusterfs.teardown.remove_bricks",
                "system.storage.glusterfs.teardown.cache_remove"
            ]

            self._apply_states(provisioner_components, self.node_list)

            self.logger.debug("Performing provisioner cleanup")
            self._run_cmd(list(map(lambda el: el + 'rm -rf ', CLEANUP_FILE_LIST)), self.node_list)

            self.logger.debug("Configuring salt at node level")
            self._run_cmd([f'sh {salt_basic_config_script}'])

            self.logger.debug("Restoring provisioner backed-up files")
            for key,val in BACKUP_FILE_DICT.items():
                if 'hosts' not in key:
                    self._run_cmd([f'yes | cp -rf {str(val)} {key}'])
                
            self._run_cmd([f'systemctl restart salt-minion salt-master'])

            # This is bit risky
            self._run_cmd([f'yes | cp -rf {BACKUP_FILE_DICT}/hosts /etc/hosts'])
            self._run_cmd(['rm -rf /root/.ssh'], self.node_list)
            self.logger.debug("Done")