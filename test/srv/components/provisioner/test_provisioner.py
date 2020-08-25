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

logger = logging.getLogger(__name__)


# TODO
#  - might makes sense. to verify for cluster case as well
#  - split into more focused scenarios
#  - tests for states relations
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('rsyslog-installed')
def test_provisioner_config_sls(
    mhostsrvnode1, cortx_hosts, configure_salt, accept_salt_keys
):
    minion_id = cortx_hosts['srvnode1']['minion_id']
    config_state = 'components.provisioner.config'
    config_file_path = '/etc/rsyslog.d/prvsnrfwd.conf'

    host = mhostsrvnode1.host
    config_file = host.file(config_file_path)
    rsyslog = host.service('rsyslog')

    # initial state: no config file, rsyslog is stopped
    host.check_output('systemctl stop rsyslog')
    assert not config_file.exists
    assert not rsyslog.is_running

    # rsyslog is not started even if configuration is changed
    host.check_output(
        "salt '{}' state.apply {}".format(minion_id, config_state)
    )
    assert config_file.exists
    assert not rsyslog.is_running

    # running rsyslog is not restarted since configuration is not changed
    host.check_output('systemctl start rsyslog')
    rsyslog_pid = host.process.get(user="root", comm="rsyslogd").pid

    host.check_output(
        "salt '{}' state.apply {}".format(minion_id, config_state)
    )
    assert rsyslog.is_running
    assert host.process.get(user="root", comm="rsyslogd").pid == rsyslog_pid

    # running rsyslog is restarted since configuration is changed
    host.check_output('rm -f {}'.format(config_file_path))
    host.check_output(
        "salt '{}' state.apply {}".format(minion_id, config_state)
    )
    assert config_file.exists
    assert rsyslog.is_running
    assert host.process.get(user="root", comm="rsyslogd").pid != rsyslog_pid
