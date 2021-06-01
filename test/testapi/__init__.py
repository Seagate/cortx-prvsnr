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

from .integration import (
    HostMeta,
    root_passwd,
    hosts_num,
    hosts_num_module,
    setup_hosts,
    setup_hosts_specs,
    ssh_profile,
    ensure_ready,
    ssh_client,
    salt_configured,
    salt_ready,
    provisioner_installed,
    provisioner_api_installed,
    cortx_mocks_deployed,
    cortx_upgrade_iso_mock_path,
    cortx_upgrade_iso_mock,
    cortx_upgrade_iso_mock_installed
)

fixtures = [
    root_passwd,
    hosts_num,
    hosts_num_module,
    setup_hosts,
    setup_hosts_specs,
    ssh_profile,
    ensure_ready,
    ssh_client,
    salt_configured,
    salt_ready,
    provisioner_installed,
    provisioner_api_installed,
    cortx_mocks_deployed,
    cortx_upgrade_iso_mock_path,
    cortx_upgrade_iso_mock,
    cortx_upgrade_iso_mock_installed
]

__all__ = [
    'HostMeta',
    'root_passwd',
    'hosts_num',
    'hosts_num_module',
    'setup_hosts',
    'setup_hosts_specs',
    'ssh_profile',
    'ensure_ready',
    'ssh_client',
    'salt_configured',
    'salt_ready',
    'provisioner_installed',
    'provisioner_api_installed',
    'cortx_mocks_deployed',
    'cortx_upgrade_iso_mock_path',
    'cortx_upgrade_iso_mock',
    'cortx_upgrade_iso_mock_installed'
]
