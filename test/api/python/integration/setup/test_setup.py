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

from . helper import RunT, SourceT

from provisioner.commands.setup_provisioner import (
    SetupProvisioner
)


logger = logging.getLogger(__name__)

# TODO parametrize per access mode: SSHPASS, bootstrap-key

# TODO IMPROVE add more checks:
#   - saltstack activ-active configuration
#   - glusterfs configuration
#   - firewall configuration
#   - etc.


@pytest.mark.isolated
def test_setup_provisioner_api(
    ask_proceed, source, custom_opts, ha,
    ssh_key, tmpdir_function, setup_hosts_specs
):
    nodes = setup_hosts_specs
    kwargs = {
        'bootstrap_key': ssh_key,
        'ha': ha,
        'profile': tmpdir_function / 'profile',
        'source': source.value,
        'update': True,
        'pypi_repo': True
    }

    if source == SourceT.ISO:
        kwargs['iso_cortx'] = custom_opts.cortx_iso

    logger.info(f"Running setup API cmd with: {nodes} {kwargs}")
    if custom_opts.interactive:
        ask_proceed()

    SetupProvisioner().run(nodes, **kwargs)


@pytest.mark.isolated
def test_setup_provisioner_cli(
    get_fixture, setup_mode_cli, run_host, ask_proceed, source, custom_opts,
    cli_cmd
):
    logger.info(f"Running cli cmd as: {cli_cmd}")
    if custom_opts.interactive:
        ask_proceed()

    if setup_mode_cli == RunT.ONTARGET_CLI:
        run_host.api_installed(local_user=True)

    run_host.check_output(
        cli_cmd, local_user=(setup_mode_cli == RunT.ONTARGET_CLI)
    )
