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
