import pytest
import logging

import test.helper as h

def test_rpm_is_buildable(rpm_prvsnr):
    pass

@pytest.mark.isolated
@pytest.mark.env_name('centos7-base')
def test_rpm_depends_on_salt_2019_2_0(host, host_rpm_prvsnr):
    depends = h.check_output(host, 'rpm -qpR {}'.format(host_rpm_prvsnr))
    assert 'salt-master = 2019.2.0\n' in depends
    assert 'salt-minion = 2019.2.0\n' in depends

@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
def test_rpm_is_installable(host, host_rpm_prvsnr):
    h.check_output(host, 'yum install -y {}'.format(host_rpm_prvsnr))
