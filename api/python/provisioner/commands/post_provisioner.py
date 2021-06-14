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

from typing import Type
# import socket
import logging

from .. import (
    inputs,
    config,
    utils
)
from ..vendor import attr
from ..config import (
    ALL_MINIONS
)
from ..pillar import PillarUpdater
from . import (
    CommandParserFillerMixin
)
from .bootstrap import (
    RunArgsSetupProvisionerGeneric,
    SetupCmdBase
)

from .bootstrap_provisioner import (
    BootstrapProvisioner
)


logger = logging.getLogger(__name__)

add_pillar_merge_prefix = PillarUpdater.add_merge_prefix


@attr.s(auto_attribs=True)
class PostProvisioner(SetupCmdBase, CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSetupProvisionerGeneric

    def run(self, nodes, **kwargs):  # noqa: C901 FIXME
        run_args = RunArgsSetupProvisionerGeneric(nodes=nodes, **kwargs)

        salt_logger = logging.getLogger('salt.fileclient')
        salt_logger.setLevel(logging.WARNING)

        # generate setup name
        setup_location = SetupCmdBase.setup_location(run_args)
        setup_name = SetupCmdBase.setup_name(run_args)

        # PREPARE FILE & PILLAR ROOTS

        logger.info(f"Starting to build setup '{setup_name}'")

        paths = config.profile_paths(
            config.profile_base_dir(
                location=setup_location, setup_name=setup_name
            )
        )

        ssh_client = BootstrapProvisioner()._create_ssh_client(
            paths['salt_master_file'], paths['salt_roster_file']
        )

        if not run_args.field_setup:
            logger.info("Generating a password for the service user")

            service_user_password = utils.generate_random_secret()

            ssh_client.cmd_run(
                (
                    'provisioner pillar_set'
                    f' system/service-user/password '
                    f' \'"{service_user_password}"\''
                ),
                targets=run_args.primary.minion_id,
                secure=True
            )

        # Grains data is not getting refreshed within sls files
        # if we call init.sls for machine_id states.
        logger.info("Refresh machine id on the system")
        for state in [
            'components.provisioner.config.machine_id.reset',
            'components.provisioner.config.machine_id.refresh_grains'
        ]:
            ssh_client.cmd_run(
                f"salt-call state.apply {state}",
                targets=ALL_MINIONS
            )

        inline_pillar = None
        if run_args.source == 'local':
            for pkg in [
                'rsyslog',
                'rsyslog-elasticsearch',
                'rsyslog-mmjsonparse'
            ]:
                ssh_client.cmd_run(
                    (
                        "provisioner pillar_set "
                        f"commons/version/{pkg} '\"latest\"'"
                    ), targets=run_args.primary.minion_id
                )
                inline_pillar = (
                    "{\"inline\": {\"no_encrypt\": True}}"
                )

        logger.info(
             "Encrypt pillar values and Refresh enclosure id on the system"
        )
        for state in [
            *(
                ()
                if run_args.source == 'local'
                else ('components.system.config.pillar_encrypt', )
            ),
            'components.system.storage.enclosure_id',
            'components.system.config.sync_salt'
        ]:
            ssh_client.cmd_run(
                f"salt-call state.apply {state}",
                targets=ALL_MINIONS
            )

        pillar = f"pillar='{inline_pillar}'" if inline_pillar else ""
        ssh_client.cmd_run(
            (
                "salt-call state.apply components.provisioner.config "
                f"{pillar}"
            ),
            targets=ALL_MINIONS
        )

        # TODO EOS-18920 Validation for node role
        # to execute cluster_id api

        logger.info("Setting unique ClusterID to pillar file "
                    f"on node: {run_args.primary.minion_id}")

        ssh_client.cmd_run(
            (
               "provisioner cluster_id"
            ), targets=run_args.primary.minion_id
        )

        logger.info("Done")
