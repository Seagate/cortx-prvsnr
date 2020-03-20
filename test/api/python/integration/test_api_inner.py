import os
import logging
import pytest
import subprocess
import json
import time
from provisioner import errors
from pathlib import Path

api_type = os.environ['TEST_API_TYPE']
assert api_type in ('py', 'cli', 'pycli')
minion_id = os.environ['TEST_MINION_ID']
nowait = (os.getenv('TEST_RUN_ASYNC', 'no') == 'yes')
get_result_tries = int(os.getenv('TEST_GET_RESULT_TRIES', 10))
salt_job = nowait or (os.getenv('PRVSNR_SALT_JOB', 'no') == 'yes')

logger = logging.getLogger(__name__)


def _api_call(fun, *args, **kwargs):
    if fun not in ('auth_init', 'get_result'):
        kwargs['nowait'] = nowait

    if api_type in ('py', 'pycli'):
        import provisioner
        provisioner.set_api(api_type)
        return getattr(provisioner, fun)(*args, **kwargs)
    else:  # cli
        _input = kwargs.pop('password', None)
        if _input is not None:
            kwargs['password'] = '-'

        kwargs['loglevel'] = 'DEBUG'
        kwargs['logstream'] = 'stderr'
        kwargs['output'] = 'json'

        cmd = ['provisioner', fun]
        for k, v in kwargs.items():
            k = '--{}'.format(k.replace('_', '-'))
            if type(v) is not bool:
                cmd.extend([k, str(v)])
            elif v:
                cmd.extend([k])
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
        return json.loads(res.stdout)['ret'] if res.stdout else None


def api_call(fun, *args, **kwargs):
    res = _api_call(fun, *args, **kwargs)
    if (fun not in ('auth_init', 'get_result')) and nowait:
        tries = 0
        while True:
            tries += 1
            # print(
            #   'Try {} for fun {}, args {}, kwargs {}'
            #   .format(tries, fun, args, kwargs)
            # )
            try:
                return _api_call('get_result', res)
            except errors.PrvsnrCmdNotFinishedError:
                if tries < get_result_tries:
                    time.sleep(1)
                else:
                    raise
    else:
        return res


salt_client = None


def run_cmd(command, retcodes=[0], **kwargs):
    from salt.client import LocalClient
    global salt_client

    if not salt_client:
        salt_client = LocalClient()

    res = salt_client.cmd('*', 'cmd.run', [command], full_return=True)
    if retcodes:
        for _id, _res in res.items():
            assert _res['retcode'] in retcodes

    return res


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
        if api_type in ('py', 'pycli'):
            from provisioner.errors import SaltError, SaltCmdRunError
            expected_exc = SaltCmdRunError if salt_job else SaltError
        else:  # cli
            from subprocess import CalledProcessError
            expected_exc = CalledProcessError

        with pytest.raises(expected_exc) as excinfo:
            api_call('pillar_get', **kwargs)

        assert expected_exc_str in str(
            type(excinfo.value.reason) if api_type in ('py', 'pycli') else
            excinfo.value.stdout
        )


def test_set_ntp():
    pillar = api_call('pillar_get')

    pillar_ntp_server = pillar['eosnode-1']['system']['ntp']['time_server']
    pillar_ntp_timezone = pillar['eosnode-1']['system']['ntp']['timezone']

    curr_params = api_call(
        'get_params', 'ntp/server', 'ntp/timezone'
    )[minion_id]

    api_ntp_server = curr_params['ntp/server']
    api_ntp_timezone = curr_params['ntp/timezone']
    assert pillar_ntp_server == api_ntp_server
    assert pillar_ntp_timezone == api_ntp_timezone

    new_ntp_server = '0.north-america.pool.ntp.org'
    new_ntp_timezone = 'Europe/Berlin'

    api_call(
        'set_ntp', server=new_ntp_server, timezone=new_ntp_timezone
    )

    curr_params = api_call(
        'get_params', 'ntp/server', 'ntp/timezone'
    )[minion_id]

    api_ntp_server = curr_params['ntp/server']
    api_ntp_timezone = curr_params['ntp/timezone']
    assert new_ntp_server == api_ntp_server
    assert new_ntp_timezone == api_ntp_timezone


# TODO slave params
def test_set_nw():
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
    api_call(
        'set_network',
        primary_hostname='host1',
        primary_floating_ip='1.2.3.4',
        primary_gateway_ip='1.2.3.4',
        primary_mgmt_ip='1.2.3.4',
        primary_mgmt_netmask='255.255.255.0',
        primary_data_ip='1.2.3.4',
        primary_data_netmask='255.255.255.0',
        slave_hostname='host2',
        slave_floating_ip='1.2.3.4',
        slave_gateway_ip='1.2.3.4',
        slave_mgmt_ip='1.2.3.4',
        slave_mgmt_netmask='255.255.255.0',
        slave_data_ip='1.2.3.4',
        slave_data_netmask='255.255.255.0',
    )

    pillar = api_call('pillar_get')

    pillar_nw_primary_mgmt_ip = pillar[
        'eosnode-1'
    ]['cluster']['eosnode-1']['network']['mgmt_nw']['ipaddr']
    pillar_nw_primary_data_ip = pillar[
        'eosnode-1'
    ]['cluster']['eosnode-1']['network']['data_nw']['ipaddr']
    pillar_nw_primary_gateway_ip = pillar[
        'eosnode-1'
    ]['cluster']['eosnode-1']['network']['gateway_ip']
    pillar_nw_primary_hostname = pillar[
        'eosnode-1'
    ]['cluster']['eosnode-1']['hostname']

    api_nw_primary_mgmt_ip = api_call(
        'get_params', 'nw_primary_mgmt_ip'
    )[minion_id]['nw_primary_mgmt_ip']
    assert pillar_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = api_call(
        'get_params', 'nw_primary_data_ip'
    )[minion_id]['nw_primary_data_ip']
    assert pillar_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = api_call(
        'get_params', 'nw_primary_gateway_ip'
    )[minion_id]['nw_primary_gateway_ip']
    assert pillar_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = api_call(
        'get_params', 'nw_primary_hostname'
    )[minion_id]['nw_primary_hostname']
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

    api_nw_primary_mgmt_ip = api_call(
        'get_params', 'nw_primary_mgmt_ip'
    )[minion_id]['nw_primary_mgmt_ip']
    assert new_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = api_call(
        'get_params', 'nw_primary_data_ip'
    )[minion_id]['nw_primary_data_ip']
    assert new_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = api_call(
        'get_params', 'nw_primary_gateway_ip'
    )[minion_id]['nw_primary_gateway_ip']
    assert new_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = api_call(
        'get_params', 'nw_primary_hostname'
    )[minion_id]['nw_primary_hostname']
    assert new_nw_primary_hostname == api_nw_primary_hostname
    '''


# TODO test for only one minion in cluster (not ALL_MINIONS)
def test_set_eosupdate_repo():
    # test_mode = os.environ['TEST_MODE']
    repo_dir = os.environ['TEST_REPO_DIR']
    iso_path = os.environ['TEST_REPO_ISO_PATH']
    base_repo_name = 'eos_update'
    prvsnr_pkg_name = 'eos-prvsnr'

    def check_unmounted(mount_dir):
        # check the record is removed from the fstab
        run_cmd(
            'grep {} /etc/fstab'.format(mount_dir),
            retcodes=[1]
        )
        # check mount point dir doesn't exist
        run_cmd(
            'ls {}'.format(mount_dir),
            retcodes=[2]
        )

    def check_not_installed(release, expected_repo_name, mount_dir=None):
        curr_params = api_call('get_params', 'eosupdate/repos')
        for _id, _params in curr_params.items():
            assert _params['eosupdate/repos'][release] is None

        curr_params = api_call(
            'get_params', 'eosupdate/repo/{}'.format(release),
        )
        for _id, _params in curr_params.items():
            assert _params['eosupdate/repo/{}'.format(release)] is None

        # check repo is not listed anymore
        run_cmd(
            'yum repolist enabled | grep {}'.format(expected_repo_name),
            retcodes=[1]
        )
        # check no any update repo is listed
        run_cmd(
            'yum repolist enabled | grep {}'.format(base_repo_name),
            retcodes=[1]
        )

        if mount_dir:
            check_unmounted(mount_dir)

    pillar = api_call('pillar_get')
    pillar_params = pillar[minion_id]['eos_release']['update']

    curr_params = api_call('get_params', 'eosupdate/repos')
    for _id, _params in curr_params.items():
        assert _params['eosupdate/repos'] == pillar_params['repos']

    # dry run check for invalid source
    if api_type == 'cli':
        from subprocess import CalledProcessError
        expected_exc = CalledProcessError
    else:
        from provisioner.errors import EOSUpdateRepoSourceError
        expected_exc = EOSUpdateRepoSourceError

    source = 'some/invalid/source'
    with pytest.raises(expected_exc) as excinfo:
        api_call(
            'set_eosupdate_repo', '1.2.3',
            source=source, dry_run=True
        )
    exc = excinfo.value
    if api_type == 'cli':
        exc = json.loads(exc.stdout)['exc']
        assert exc['type'] == 'EOSUpdateRepoSourceError'
        assert exc['args'] == [source, 'unexpected type of source']
    else:
        assert type(exc).__name__ == 'EOSUpdateRepoSourceError'
        assert exc.source == source
        assert exc.reason == 'unexpected type of source'

    for release, source, expected_rpm_name in [
        ('1.2.3', repo_dir, prvsnr_pkg_name),
        ('1.2.4', iso_path, prvsnr_pkg_name),
        (
            '1.2.5',
            'http://mirror.ghettoforge.org/distributions/gf/el/7/gf/x86_64/',
            'gf-release'
        )  # just for an example
    ]:
        expected_repo_name = '{}_{}'.format(base_repo_name, release)

        if source is iso_path:
            mount_dir = Path(pillar_params['base_dir']) / release
        else:
            mount_dir = None

        expected_source = (
            'dir' if source is repo_dir else
            'iso' if source is iso_path else
            source
        )

        # INSTALL
        api_call(
            'set_eosupdate_repo', release, source=source
        )

        curr_params = api_call('get_params', 'eosupdate/repos')
        for _id, _params in curr_params.items():
            assert _params['eosupdate/repos'][release] == expected_source

        curr_params = api_call(
            'get_params', 'eosupdate/repo/{}'.format(release)
        )
        for _id, _params in curr_params.items():
            assert _params[
                'eosupdate/repo/{}'.format(release)
            ] == expected_source

        # check repo is enabled
        run_cmd(
            'yum repolist enabled | grep {}'.format(expected_repo_name)
        )
        # check only one update repo is enabled
        res = run_cmd(
            'yum repolist enabled | grep {}'.format(base_repo_name)
        )
        for _id, _res in res.items():
            assert len(_res['ret'].strip().split(os.linesep)) == 1
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
            source=undefined_value
        )
        check_not_installed(release, expected_repo_name, mount_dir)

        # dry run check
        api_call(
            'set_eosupdate_repo',
            release,
            source=source,
            dry_run=True
        )
        #   verify that nothing has changed in the system
        check_not_installed(release, expected_repo_name, mount_dir)


def test_set_eosupdate_repo_for_reinstall():
    repo_dir = os.environ['TEST_REPO_DIR']
    test_file_path = os.environ['TEST_FILE_PATH']
    # base_repo_name = 'eos_update'
    prvsnr_pkg_name = 'eos-prvsnr'

    release = '1.2.3'
    source = repo_dir
    # expected_rpm_name = prvsnr_pkg_name

    # INSTALL
    api_call(
        'set_eosupdate_repo', release, source=source, targets=minion_id
    )

    run_cmd(
        "yum reinstall {}".format(prvsnr_pkg_name)
    )

    from provisioner.config import PRVSNR_ROOT_DIR
    assert (PRVSNR_ROOT_DIR / test_file_path).exists()


# TODO for now just tests that repo is installed and yum able
#      to start installation (which will definitely fail)
#   - install eos stack first from some release
#   - set some newer release
#   - call udpate
def test_eos_update():
    api_call(
        'set_eosupdate_repo',
        '1.2.3',
        source='http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/last_successful',  # noqa: E501
        targets=minion_id
    )

    api_call('eos_update', targets=minion_id)
