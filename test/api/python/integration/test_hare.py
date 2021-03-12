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

test_status_offline_fname = 'pcs.status.offline.out'
test_status_online_fname = 'pcs.status.online.out'
test_stop_fname = 'pcs.cluster.stop.all.out'
test_start_fname = 'pcs.cluster.start.all.out'


pcs_mock_tmpl = '''
    if [[ "$1 $2" == "cluster stop" ]]; then
        cat {stop_out}
    elif [[ "$1 $2" == "cluster start" ]]; then
        cat {start_out}
        echo 1 >/tmp/pcs.starting
    elif [[ "$1" == 'status' ]]; then
        if [[ -f /tmp/pcs.starting ]]; then
            try="$(cat /tmp/pcs.starting)"
            try=$(( $try + 1 ))
            echo $try >/tmp/pcs.starting

            if [[ "$try" -gt 5 ]]; then
                cat {status_online_out}
            else
                cat {status_offline_out}
            fi
        else
            cat {status_offline_out}
        fi
    else
        echo "Unexpected args: <$@>"
        exit 1
    fi
'''


@pytest.mark.skip(reason="EOS-18738")
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
def test_cluster_mgmt(
    mhostsrvnode1, run_test, request, test_output_dir
):
    pcs_mock = pcs_mock_tmpl.format(
        stop_out=mhostsrvnode1.copy_to_host(
            test_output_dir / test_stop_fname
        ),
        start_out=mhostsrvnode1.copy_to_host(
            test_output_dir / test_start_fname
        ),
        status_offline_out=mhostsrvnode1.copy_to_host(
            test_output_dir / test_status_offline_fname
        ),
        status_online_out=mhostsrvnode1.copy_to_host(
            test_output_dir / test_status_online_fname
        )
    )
    request.applymarker(pytest.mark.mock_cmds(
        {'srvnode1': [{'pcs': pcs_mock}]})
    )
    request.getfixturevalue('mock_hosts')
    run_test(mhostsrvnode1)
