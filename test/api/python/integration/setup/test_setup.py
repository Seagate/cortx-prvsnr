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

import pytest
import logging

# from provisioner.commands.setup_provisioner import (
#     SetupProvisioner
# )


logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def root_passwd():
    return 'root'


@pytest.mark.isolated
def test_setup_cluster(
    request, env_provider,  logdir_host, safe_function_name,
    root_passwd, mlocalhost, custom_opts, tmpdir_function,
    ask_proceed
    # , ssh_key,
):
    nodes_num = 3
    request.applymarker(
        pytest.mark.hosts([f'srvnode{i}' for i in range(1, nodes_num + 1)])
    )

    mhosts = [
        request.getfixturevalue(f'mhostsrvnode{i}')
        for i in range(1, nodes_num + 1)
    ]

    for mhost in mhosts:
        mhost.check_output(f'echo {root_passwd} | passwd --stdin root')

        if env_provider == 'vbox':
            mhost.remote.cmd(
               'snapshot', 'save', mhost.remote.name, 'initial --force'
            )
        elif env_provider == 'docker':
            mhost.check_output('touch /etc/fstab')

    # primary = mhosts[0]
    # primary.api_installed(local_user=True)

    log_opts = ''
    # if logdir_host:
    #    logfile = logdir_host / safe_function_name.with_suffix('.setup.log')
    #    log_opts = f"--logfile --logfile-filename {logfile}"

    if custom_opts.logdir:
        logfile = custom_opts.logdir / safe_function_name.with_suffix('.setup.log')
    else:
        logfile = tmpdir_function / 'setup.log'

    log_opts = f"--logfile --logfile-filename {logfile}"

    nodes = [
        f"srvnode-{i + 1}:{mhosts[i].ssh_host}" for i in range(nodes_num)
    ]


    # cmd = (
    #     f"SSHPASS={root_passwd} provisioner setup_provisioner"
    #     f" --source local --local-repo {primary.repo} --ha"
    #     f" {log_opts}"
    #     f" {' '.join(nodes)}"
    # )
    cmd = (
        f"SSHPASS={root_passwd} provisioner setup_provisioner"
        f" --source local --ha"
        f" {log_opts}"
        f" {' '.join(nodes)}"
    )

    logger.info(f"Starting setup_provisioner as: {cmd}")

    ask_proceed()
    # primary.check_output(cmd, local_user=True)
    mlocalhost.check_output(cmd)

    # nodes = [
    #     f'srvnode-1:{mhostsrvnode1.ssh_host}',
    #     f'srvnode-2:{mhostsrvnode2.ssh_host}'
    # ]
    # kwargs = {
    #     'bootstrap_key': ssh_key,
    #     'ha': True,
    #     'profile': tmpdir_function / 'test-setup',
    #     'source': 'local',
    #     'update': True
    # }
    #
    # SetupProvisioner().run(nodes, **kwargs)
    # TODO IMPROVE add more checks:
    #   - saltstack activ-active configuration
    #   - glusterfs configuration
    #   - firewall configuration
    #   - etc.
