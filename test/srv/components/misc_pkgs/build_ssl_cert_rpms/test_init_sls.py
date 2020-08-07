#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
    # TODO improve later once we have more flexible state parametrization per roles
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
        "salt '*' state.apply components.system.config.setup_ssh"
    )

    for label in ('srvnode1', 'srvnode2'):
        mhostsrvnode1.check_output(
            "salt '{}' state.apply components.misc_pkgs.build_ssl_cert_rpms".format(
                cortx_hosts[label]['minion_id']
            )
        )

    # TODO check expected changes on nodes
