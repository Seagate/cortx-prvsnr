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
from copy import deepcopy
from collections import defaultdict

from provisioner.commands import GetReleaseVersion


logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_level():
    return 'upgrade-env-ready'


@pytest.fixture
def hosts_spec(hosts_spec, hosts):
    res = deepcopy(hosts_spec)
    for host in hosts:
        docker_settings = res[host]['remote']['specific']
        docker_settings['docker'] = defaultdict(
            dict, docker_settings.get('docker', {})
        )
        docker_settings = docker_settings['docker']
        docker_settings['privileged'] = True

        docker_settings['volumes']['/dev'] = {
            'bind': '/dev', 'mode': 'ro'
        }
    return res


cortx_mock_tmpl = '''
if [[ "$1" == "--help" ]]; then
    echo 'cortx help'
elif [[ "$1 $2" == "cluster stop" ]]; then
    echo '{"status": "Succeeded"}'
    rm -rf /tmp/start
    touch /tmp/stop
elif [[ "$1 $2" == "cluster start" ]]; then
    echo '{"status": "Succeeded"}'
    rm -rf /tmp/stop
    touch /tmp/start
elif [[ "$1 $2" == "cluster status" ]]; then
    if [[ -f /tmp/stop ]]; then
        echo '{"status": "Succeeded", "output": "offline"}'
        rm -rf /tmp/stop
    else
        echo '{"status": "Succeeded", "output": "online"}'
        rm -rf /tmp/start
    fi
else
    echo "Unexpected args: <$@>"
    exit 1
fi
'''


pcs_mock_tmpl = '''
if [[ "$1" == "--help" ]]; then
    echo 'pcs help'
elif [[ "$1 $2" == "cluster stop" ]]; then
    rm -rf /tmp/start
    touch /tmp/stop
elif [[ "$1 $2" == "cluster start" ]]; then
    rm -rf /tmp/stop
    touch /tmp/start
elif [[ "$1" == "status" ]]; then
    if [[ -f /tmp/stop ]]; then
        echo OFFLINE:
        rm -rf /tmp/stop
    else
        rm -rf /tmp/start
    fi
else
    echo "Unexpected args: <$@>"
    exit 1
fi
'''


@pytest.fixture
def mock_system_cmds(hosts, request):
    request.applymarker(
        pytest.mark.mock_cmds({
            list(hosts)[0]: [
                {'cortx': cortx_mock_tmpl},
                {'pcs': pcs_mock_tmpl}
            ]
        })
    )
    request.getfixturevalue('mock_hosts')


# main goals:
#   - verify delegation of orchestration to a new version
#   - verify salt based call work fine (mini API)
@pytest.mark.verified
@pytest.mark.hosts_num(3)
@pytest.mark.isolated
def test_swupgrade_r2_offline(
    setup_hosts,
    mock_system_cmds,
    ssh_client,
    salt_ready,
    request
):
    # upgrade ISO prepared (with mocks):
    #   - TODO HA setup.yaml includes pre/post flag on cluster level

    # FIXME hard-coded
    upgrade_iso = '/var/lib/seagate/cortx/provisioner/local/cortx_repos/upgrade_mock_2.1.0.iso'  # noqa: E501
    run_host = setup_hosts[0]
    old_ver = '2.0.0-177'
    new_ver = '2.1.0-177'

    # logic (HAPPY PATH):
    run_host.check_output(
        f"provisioner set_swupgrade_repo {upgrade_iso}"
    )
    run_host.check_output(
        "provisioner sw_upgrade --offline"
    )

    # CHECKS

    # CLUSTER level

    # new Cortx version is running
    # FIXME hard-coded
    metadata = run_host.check_output(
        "provisioner get_release_version"
    )
    assert GetReleaseVersion.cortx_version(metadata) == new_ver

    #           - new provisioner API vesion was called to manage the logic
    #             with --noprepare flag
    #           - node level logic was applied for all the nodes concurrently
    #           - cluster level logic:
    #               - HA standby
    #               - HA pre upgrade
    #               - cluster stop
    #               - node level logic
    #               - HA post upgrade
    #               - cluster start
    #       - NODE level
    #           - upgrade for sw was applied in predefined order
    #           - mini APIs: (TODO separate test for setup.yaml spec)
    #               - called on NODE level
    #               - HA: were called for CLUSTER level as well
    #
    # FIXME hard-coded mock output

    def mock_str(flow, level, hook, old_ver=None, new_ver=None):
        res = (
            f"{flow} {level} {hook} "
            f"PRVSNR_MINI_FLOW={flow},"
            f"PRVSNR_MINI_LEVEL={level},"
            f"PRVSNR_MINI_HOOK={hook}"
        )
        if old_ver:
            res += ",CORTX_VERSION={old_ver}"
        if new_ver:
            res += ",CORTX_UPGRADE_VERSION={new_ver}"
        return res

    assert (
        run_host.check_output(
            "grep ha: /tmp/mock.log | awk '{print $3 FS $4 FS $6 FS $7}'"
        ) == (
            f"{mock_str('upgrade-offline', 'cluster', 'backup')}\n"
            f"{mock_str('upgrade-offline', 'cluster', 'pre-upgrade', old_ver, new_ver)}\n"  # noqa: E501
            f"{mock_str('upgrade-offline', 'node', 'backup')}\n"
            f"{mock_str('upgrade-offline', 'node', 'pre-upgrade', old_ver, new_ver)}\n"  # noqa: E501
            f"{mock_str('upgrade-offline', 'node', 'post-upgrade', old_ver, new_ver)}\n"  # noqa: E501
            f"{mock_str('upgrade-offline', 'cluster', 'post-upgrade', old_ver, new_ver)}"  # noqa: E501
        )
    )

    # other nodes should receive only node level events
    for host in setup_hosts[1:]:
        assert (
            host.check_output(
                "grep ha: /tmp/mock.log | awk '{print $3 FS $4 FS $6 FS $7}'"
            ) == (
                "{mock_str('upgrade-offline', 'node', 'backup')}\n"
                "{mock_str('upgrade-offline', 'node', 'pre-upgrade', old_ver, new_ver)}\n"  # noqa: E501
                "{mock_str('upgrade-offline', 'node', 'post-upgrade', old_ver, new_ver)}"  # noqa: E501
            )
        )
    #           - HA mini APIs were called for cluster level as well
    #             (separate test for setup.yaml spec)
    #
    # XXX:
    #   - mini provisioner calls should be done on NODE level
    #       - current implementation - SW level
    #   - migrate -> post-upgrade
    #
