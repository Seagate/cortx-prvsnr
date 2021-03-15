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

logger = logging.getLogger(__name__)


# TODO
#  - might makes sense. to verify for cluster case as well
#  - split into more focused scenarios
#  - tests for states relations
@pytest.mark.skip(reason="EOS-18738")
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
