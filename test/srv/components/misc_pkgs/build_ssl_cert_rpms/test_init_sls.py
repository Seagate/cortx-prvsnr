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

from test.helper import PRVSNR_REPO_INSTALL_DIR

logger = logging.getLogger(__name__)


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.hosts(['srvnode1', 'srvnode2'])
@pytest.mark.skip(reason="EOS-4907")
def test_build_ssl_cert_rpms_appliance(
    mhostsrvnode1, mhostsrvnode2, cortx_hosts, configure_salt, accept_salt_keys
):
    # enable cluster setup
    # TODO improve later once we have more flexible
    #      state parametrization per roles
    mhostsrvnode1.check_output(
        "sed -i 's/# - srvnode-2/- srvnode-2/g' {}".format(
            PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / 'cluster.sls'
        )
    )
    mhostsrvnode1.check_output(
        "sed -i 's/type: single/type: dual/g' {}".format(
            PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / 'cluster.sls'
        )
    )

    mhostsrvnode1.check_output(
        "salt '*' state.apply system.config.setup_ssh"
    )

    for label in ('srvnode1', 'srvnode2'):
        mhostsrvnode1.check_output(
            "salt '{}' state.apply misc_pkgs.build_ssl_cert_rpms"
            .format(cortx_hosts[label]['minion_id'])
        )

    # TODO check expected changes on nodes
