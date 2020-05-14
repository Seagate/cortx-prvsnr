import pytest
import logging

logger = logging.getLogger(__name__)


# TODO
#  - might makes sense. to verify for cluster case as well
#  - split into more focused scenarios
#  - tests for states relations
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
@pytest.mark.env_level('rsyslog-installed')
def test_provisioner_config_sls(
    mhosteosnode1, eos_hosts, configure_salt, accept_salt_keys
):
    minion_id = eos_hosts['eosnode1']['minion_id']
    config_state = 'components.provisioner.config'
    config_file_path = '/etc/rsyslog.d/prvsnrfwd.conf'

    host = mhosteosnode1.host
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
