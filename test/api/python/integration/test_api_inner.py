import os
import logging
import pytest
import subprocess
from pathlib import Path

api_type = os.environ['TEST_API_TYPE']
assert api_type in ('py', 'cli', 'pycli')
minion_id = os.environ['TEST_MINION_ID']

logger = logging.getLogger(__name__)


def api_call(fun, *args, **kwargs):
    if api_type in ('py', 'pycli'):
        import provisioner
        provisioner.set_api(api_type)
        return getattr(provisioner, fun)(*args, **kwargs)
    else:  # cli
        import json

        _input = kwargs.pop('password', None)
        if _input is not None:
            kwargs['password'] = '-'

        kwargs['loglevel'] = 'DEBUG'
        kwargs['logstream'] = 'stderr'
        kwargs['output'] = 'json'

        cmd = ['provisioner', fun]
        for k, v in kwargs.items():
            cmd.extend(['--{}'.format(k), str(v)])
        cmd.extend([str(a) for a in args])
        logger.debug("Command: {}".format(cmd))

        res = subprocess.run(
            cmd,
            input=_input,
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return json.loads(res.stdout) if res.stdout else None


def run_cmd(command, **kwargs):
    _kwargs = dict(
        shell=True,
        check=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _kwargs.update(kwargs)
    return subprocess.run(command, **_kwargs)


def test_external_auth():
    kwargs = {}
    username = os.environ['TEST_USERNAME']
    password = os.environ['TEST_PASSWORD']
    expected_exc_str = os.environ.get('TEST_ERROR')

    if username:
        if api_type in ('py', 'pycli'):
            api_call('auth_init', username=username, password=password)
        else:  # cli
            kwargs['username'] = username
            kwargs['password'] = password

    if expected_exc_str is None:
        api_call('pillar_get', **kwargs)
    else:
        if api_type == 'py':
            from provisioner.errors import SaltError
            expected_exc = SaltError
        elif api_type == 'pycli':
            from provisioner.errors import ProvisionerError
            expected_exc = ProvisionerError
        else:  # cli
            from subprocess import CalledProcessError
            expected_exc = CalledProcessError

        with pytest.raises(expected_exc) as excinfo:
            api_call('pillar_get', **kwargs)

        assert expected_exc_str in str(
            excinfo.value if api_type in ('py', 'pycli') else excinfo.value.stderr
        )


def test_ntp_configuration():
    pillar = api_call('pillar_get')

    pillar_ntp_server = pillar['eosnode-1']['system']['ntp']['time_server']
    pillar_ntp_timezone = pillar['eosnode-1']['system']['ntp']['timezone']

    curr_params = api_call('get_params', 'ntp/server', 'ntp/timezone')[minion_id]

    api_ntp_server = curr_params['ntp/server']
    api_ntp_timezone = curr_params['ntp/timezone']
    assert pillar_ntp_server == api_ntp_server
    assert pillar_ntp_timezone == api_ntp_timezone

    new_ntp_server = '0.north-america.pool.ntp.org'
    new_ntp_timezone = 'Europe/Berlin'

    api_call('set_ntp', server=new_ntp_server, timezone=new_ntp_timezone)

    curr_params = api_call('get_params', 'ntp/server', 'ntp/timezone')[minion_id]

    api_ntp_server = curr_params['ntp/server']
    api_ntp_timezone = curr_params['ntp/timezone']
    assert new_ntp_server == api_ntp_server
    assert new_ntp_timezone == api_ntp_timezone


# TODO slave params
def test_network_configuration():
    params = (
        'primary_hostname',
        'primary_floating_ip',
        'primary_gateway_ip',
        'primary_mgmt_ip',
        'primary_mgmt_netmask',
        'primary_data_ip',
        'primary_data_netmask',
        'slave_hostname',
        'slave_floating_ip',
        'slave_gateway_ip',
        'slave_mgmt_ip',
        'slave_mgmt_netmask',
        'slave_data_ip',
        'slave_data_netmask'
    )

    api_call(
        'get_params',
        *["network/{}".format(p) for p in params],
        targets=minion_id
    )

    '''
    pillar = api_call('pillar_get')

    pillar_nw_primary_mgmt_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['mgmt_nw']['ipaddr']
    pillar_nw_primary_data_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['data_nw']['ipaddr']
    pillar_nw_primary_gateway_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['gateway_ip']
    pillar_nw_primary_hostname = pillar['eosnode-1']['cluster']['eosnode-1']['hostname']

    api_nw_primary_mgmt_ip = api_call('get_params', 'nw_primary_mgmt_ip')[minion_id]['nw_primary_mgmt_ip']
    assert pillar_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = api_call('get_params', 'nw_primary_data_ip')[minion_id]['nw_primary_data_ip']
    assert pillar_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = api_call('get_params', 'nw_primary_gateway_ip')[minion_id]['nw_primary_gateway_ip']
    assert pillar_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = api_call('get_params', 'nw_primary_hostname')[minion_id]['nw_primary_hostname']
    assert pillar_nw_primary_hostname == api_nw_primary_hostname

    # TODO what values is bettwe to use here ???
    new_nw_primary_mgmt_ip = '192.168.7.7'
    new_nw_primary_data_ip = '192.168.7.8'
    new_nw_primary_gateway_ip = '192.168.7.9'
    new_nw_primary_hostname = 'new-hostname'

    api_call(
        'set_network',
        primary_mgmt_ip=new_nw_primary_mgmt_ip,
        primary_data_ip=new_nw_primary_data_ip,
        primary_gateway_ip=new_nw_primary_gateway_ip,
        primary_hostname=new_nw_primary_hostname
    )

    api_nw_primary_mgmt_ip = api_call('get_params', 'nw_primary_mgmt_ip')[minion_id]['nw_primary_mgmt_ip']
    assert new_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = api_call('get_params', 'nw_primary_data_ip')[minion_id]['nw_primary_data_ip']
    assert new_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = api_call('get_params', 'nw_primary_gateway_ip')[minion_id]['nw_primary_gateway_ip']
    assert new_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = api_call('get_params', 'nw_primary_hostname')[minion_id]['nw_primary_hostname']
    assert new_nw_primary_hostname == api_nw_primary_hostname
    '''


def test_eosupdate_repo_configuration():
    repo_dir = os.environ['TEST_REPO_DIR']
    iso_path = os.environ['TEST_REPO_ISO_PATH']

    def check_unmounted(mount_dir):
        # check the record is removed from the fstab
        res = run_cmd(
            'grep {} /etc/fstab'.format(mount_dir),
            check=False
        )
        assert res.returncode == 1
        # check mount point dir doesn't exist
        res = run_cmd(
            'ls {}'.format(mount_dir),
            check=False
        )
        assert res.returncode == 2

    pillar = api_call('pillar_get')
    pillar_params = pillar[minion_id]['eos_release']['update']

    curr_params = api_call('get_params', 'eosupdate/repos', targets=minion_id)[minion_id]
    assert curr_params['eosupdate/repos'] == pillar_params['repos']

    base_repo_name = 'eos_update'
    prvsnr_cli_pkg_name = 'eos-prvsnr'
    for release, source, expected_rpm_name in [
        ('1.2.3', repo_dir, prvsnr_cli_pkg_name),
        ('1.2.4', iso_path, prvsnr_cli_pkg_name),
        (
            '1.2.5',
            'http://mirror.ghettoforge.org/distributions/gf/el/7/gf/x86_64/',
            'gf-release'
        )  # just for an example
    ]:
        expected_repo_name = '{}_{}'.format(base_repo_name, release)

        if source is iso_path:
            mount_dir = Path(pillar_params['mount_base_dir']) / release
        else:
            mount_dir = None

        # INSTALL
        api_call(
            'set_eosupdate_repo', release, source=source, targets=minion_id
        )

        expected_source = (
            "file://{}".format(source) if source is repo_dir else source
        )

        curr_params = api_call('get_params', 'eosupdate/repos', targets=minion_id)[minion_id]
        assert curr_params['eosupdate/repos'][release] == expected_source

        curr_params = api_call(
            'get_params', 'eosupdate/repo/{}'.format(release),
            targets=minion_id
        )[minion_id]
        assert curr_params['eosupdate/repo/{}'.format(release)] == expected_source

        # check repo is enabled
        run_cmd(
            'yum repolist enabled | grep {}'.format(expected_repo_name)
        )
        # check only one update repo is enabled
        res = run_cmd(
            'yum repolist enabled | grep {}'.format(base_repo_name)
        )
        assert len(res.stdout.strip().split(os.linesep)) == 1
        # check rpm is available
        run_cmd(
            "yum list available | grep '^{}.*{}$'"
            .format(expected_rpm_name, expected_repo_name)
        )

        if api_type in ('py', 'pycli'):
            from provisioner import UNDEFINED
            undefined_value = UNDEFINED
        else:
            undefined_value = 'PRVSNR_UNDEFINED'

        # REMOVE
        # TODO UNDEFINED
        api_call(
            'set_eosupdate_repo',
            release,
            source=undefined_value,
            targets=minion_id
        )

        curr_params = api_call('get_params', 'eosupdate/repos', targets=minion_id)[minion_id]
        assert curr_params['eosupdate/repos'][release] is None

        curr_params = api_call(
            'get_params', 'eosupdate/repo/{}'.format(release),
            targets=minion_id
        )[minion_id]
        assert curr_params['eosupdate/repo/{}'.format(release)] is None

        # check repo is not listed anymore
        res = run_cmd(
            'yum repolist enabled | grep {}'.format(expected_repo_name),
            check=False
        )
        assert res.returncode == 1
        # check no any update repo is listed
        res = run_cmd(
            'yum repolist enabled | grep {}'.format(base_repo_name),
            check=False
        )
        assert res.returncode == 1

        if mount_dir:
            check_unmounted(mount_dir)


# TODO for now just tests that repo is installed and yum able to start installation (which will definitely fail)
#   - install eos stack first from some release
#   - set some newer release
#   - call udpate
def test_eos_update():
    api_call(
        'set_eosupdate_repo',
        '1.2.3',
        source='http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/last_successful',
        targets=minion_id
    )

    api_call('eos_update', targets=minion_id)
