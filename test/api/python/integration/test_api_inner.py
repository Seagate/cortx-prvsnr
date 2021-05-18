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

import os
import logging
import pytest
import subprocess
import time
from pathlib import Path

api_type = os.environ['TEST_API_TYPE']
assert api_type in ('py', 'cli', 'pycli')
minion_id = os.environ['TEST_MINION_ID']
nowait = (os.getenv('TEST_RUN_ASYNC', 'no') == 'yes')
get_result_tries = int(os.getenv('TEST_GET_RESULT_TRIES', 30))
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
        from provisioner._api_cli import (
            api_args_to_cli, process_cli_result
        )
        _input = kwargs.pop('password', None)
        if _input is not None:
            kwargs['password'] = '-'

        kwargs['console'] = True
        kwargs['console-level'] = 'DEBUG'
        kwargs['console-stream'] = 'stderr'

        cmd = ['provisioner']
        cmd.extend(api_args_to_cli(fun, *args, **kwargs))
        logger.debug("Command: {}".format(cmd))

        env = os.environ.copy()
        env.update({'PRVSNR_OUTPUT': 'json'})

        try:
            res = subprocess.run(
                cmd,
                env=env,
                input=_input,
                check=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as exc:
            return process_cli_result(exc.stdout, exc.stderr)
        else:
            return process_cli_result(res.stdout, res.stderr)


def api_call(fun, *args, **kwargs):
    from provisioner.errors import PrvsnrCmdNotFinishedError

    username = kwargs.get('username')
    password = kwargs.get('password')
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
                _kwargs = {}
                if username:
                    _kwargs['username'] = username
                    _kwargs['password'] = password
                return _api_call(
                    'get_result', res, **_kwargs
                )
            except PrvsnrCmdNotFinishedError:
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
        from provisioner.errors import SaltError, SaltCmdRunError
        expected_exc = SaltCmdRunError if salt_job else SaltError

        with pytest.raises(expected_exc) as excinfo:
            api_call('pillar_get', **kwargs)

        assert expected_exc_str in str(type(excinfo.value.reason))


# TODO multiminion case verification
# TODO test pillar_get without params
def test_pillar_get_set():
    from provisioner.config import (
        PRVSNR_PILLAR_DIR,
        PRVSNR_USER_PILLAR_HOST_DIR_TMPL,
        PRVSNR_USER_PILLAR_ALL_HOSTS_DIR
    )

    kp_simple = 'test/simple'
    kp_dict = 'test/dict'
    kp_list = 'test/list'

    test_pillar_sls = Path(f"{PRVSNR_PILLAR_DIR}/components/cluster.sls")
    test_pillar_sls_data = test_pillar_sls.read_text()

    pillar = api_call('pillar_get')
    pillar_partial = api_call(
        'pillar_get', kp_simple, kp_dict,  kp_list
    )

    for m_id, data in pillar.items():
        assert data['test']['simple'] == pillar_partial[m_id][kp_simple]
        assert data['test']['dict'] == pillar_partial[m_id][kp_dict]
        assert data['test']['list'] == pillar_partial[m_id][kp_list]

    # default targetting
    for kp, value in (
        (kp_simple, 2),
        (kp_dict, {'2': {'3': 44}}),
        (kp_list, ['a', 'b', '3', 2, {'1': 0}]),
    ):
        assert pillar_partial[minion_id][kp] != value

        api_call('pillar_set', kp, value)
        new_pillar = api_call('pillar_get', kp)

        # pillar was properly updated
        assert new_pillar[minion_id][kp] == value
        # test pillar file in default location is unchanged
        assert test_pillar_sls.read_text() == test_pillar_sls_data

    # check pillar sls file
    assert (PRVSNR_USER_PILLAR_ALL_HOSTS_DIR / 'test.sls').exists()

    pillar_partial = api_call(
        'pillar_get', kp_simple, kp_dict,  kp_list
    )

    # specific minion targetting
    # someminion_id = 'someminion'
    for kp, value in (
        (kp_simple, 3),
        (kp_dict, {'2': {'3': 444}}),
        (kp_list, ['aa', 'bb', '33', 22, {'11': 0}]),
    ):
        assert pillar_partial[minion_id][kp] != value

        # TODO check with another minion
        # targetting another minion
        # api_call('pillar_set', kp, value, targets=someminion_id)
        # new_pillar = api_call('pillar_get', kp)
        # pillar for this minion wasn't updated
        # assert new_pillar[minion_id][kp] == pillar_partial[minion_id][kp]

        # targetting this minion
        api_call('pillar_set', kp, value, targets=minion_id)
        new_pillar = api_call('pillar_get', kp)
        # pillar was properly updated
        assert new_pillar[minion_id][kp] == value

        # test pillar file in default location is unchanged
        assert test_pillar_sls.read_text() == test_pillar_sls_data

    # check pillar sls files
    # assert (
    #     PRVSNR_USER_PILLAR_HOST_DIR_TMPL.format(
    #       minion_id=someminion_id
    #     ) / 'test.sls'
    # ).exists()
    assert (
        Path(
            PRVSNR_USER_PILLAR_HOST_DIR_TMPL.format(minion_id=minion_id)
        ) / 'test.sls'
    ).exists()

    # fpath verification
    fpath = 'test2.sls'
    api_call('pillar_set', kp, value, fpath=fpath)
    assert (PRVSNR_USER_PILLAR_ALL_HOSTS_DIR / fpath).exists()
    api_call('pillar_set', kp, value, fpath=fpath, targets=minion_id)
    assert (
        Path(PRVSNR_USER_PILLAR_HOST_DIR_TMPL.format(minion_id=minion_id)) /
        fpath
    ).exists()


def test_set_ntp():
    pillar = api_call('pillar_get')

    pillar_ntp_server = pillar['srvnode-1']['system']['ntp']['time_server']
    pillar_ntp_timezone = pillar['srvnode-1']['system']['ntp']['timezone']

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


# TODO IMPROVE need a good scenario, for now just gets values
def test_set_network():
    from provisioner.api_spec import param_spec
    api_call(
        'get_params',
        *[p for p in param_spec if str(Path(p).parent) == 'network'],
        targets=minion_id
    )

    '''
    api_call(
        'set_network',
        primary_hostname='host1',
        primary_data_roaming_ip='1.2.3.4',
        primary_gateway_ip='1.2.3.4',
        primary_mgmt_public_ip='1.2.3.4',
        primary_mgmt_netmask='255.255.255.0',
        primary_data_public_ip='1.2.3.4',
        primary_data_netmask='255.255.255.0',
        secondary_hostname='host2',
        secondary_floating_ip='1.2.3.4',
        secondary_gateway_ip='1.2.3.4',
        secondary_mgmt_public_ip='1.2.3.4',
        secondary_mgmt_netmask='255.255.255.0',
        secondary_data_public_ip='1.2.3.4',
        secondary_data_netmask='255.255.255.0',
    )

    pillar = api_call('pillar_get')

    pillar_nw_primary_mgmt_ip = pillar[
        'srvnode-1'
    ]['cluster']['srvnode-1']['network']['mgmt']['public_ip']
    pillar_nw_primary_data_ip = pillar[
        'srvnode-1'
    ]['cluster']['srvnode-1']['network']['data']['public_ip']
    pillar_nw_primary_gateway_ip = pillar[
        'srvnode-1'
    ]['cluster']['srvnode-1']['network']['gateway_ip']
    pillar_nw_primary_hostname = pillar[
        'srvnode-1'
    ]['cluster']['srvnode-1']['hostname']

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
        primary_mgmt_public_ip=new_nw_primary_mgmt_ip,
        primary_data_public_ip=new_nw_primary_data_ip,
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
def test_set_swupdate_repo():  # noqa: C901 FIXME
    # test_mode = os.environ['TEST_MODE']
    repo_dir = os.environ['TEST_REPO_DIR']
    iso_path = os.environ['TEST_REPO_ISO_PATH']
    base_repo_name = 'cortx_update'
    prvsnr_pkg_name = 'cortx-prvsnr'

    def check_mount_not_in_fstab(mount_dir):
        run_cmd(
            'grep {} /etc/fstab'.format(mount_dir),
            retcodes=[1]
        )

    def check_unmounted(mount_dir):
        check_mount_not_in_fstab(mount_dir)
        # check mount point dir doesn't exist
        run_cmd(
            'ls {}'.format(mount_dir),
            retcodes=[2]
        )

    def check_not_installed(release, expected_repo_name, mount_dir=None):
        curr_params = api_call('get_params', 'swupdate/repos')
        for _id, _params in curr_params.items():
            assert _params['swupdate/repos'][release] is None

        curr_params = api_call(
            'get_params', 'swupdate/repo/{}'.format(release),
        )
        for _id, _params in curr_params.items():
            assert _params['swupdate/repo/{}'.format(release)] is None

        # check repo is not listed anymore
        run_cmd(
            'yum repolist enabled | grep {}'.format(expected_repo_name),
            retcodes=[1]
        )

        if mount_dir:
            check_unmounted(mount_dir)

    pillar = api_call('pillar_get')
    pillar_params = pillar[minion_id]['cortx_release']['update']

    curr_params = api_call('get_params', 'swupdate/repos')
    for _id, _params in curr_params.items():
        assert _params['swupdate/repos'] == pillar_params['repos']

    # dry run check for invalid source
    from provisioner.errors import SWUpdateRepoSourceError
    expected_exc = SWUpdateRepoSourceError

    source = 'some/invalid/source'
    with pytest.raises(expected_exc) as excinfo:
        api_call(
            'set_swupdate_repo', '1.2.3',
            source=source, dry_run=True
        )
    exc = excinfo.value
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

        # to check that base_dir will be created during repo install
        run_cmd(
            'rm -rf {}'.format(pillar_params['base_dir'])
        )

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
            'set_swupdate_repo', release, source=source
        )

        curr_params = api_call('get_params', 'swupdate/repos')
        for _id, _params in curr_params.items():
            assert _params['swupdate/repos'][release] == expected_source

        curr_params = api_call(
            'get_params', 'swupdate/repo/{}'.format(release)
        )
        for _id, _params in curr_params.items():
            assert _params[
                'swupdate/repo/{}'.format(release)
            ] == expected_source

        if mount_dir:
            check_mount_not_in_fstab(mount_dir)

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
            'set_swupdate_repo',
            release,
            source=undefined_value
        )
        check_not_installed(release, expected_repo_name, mount_dir)
        # check no any update repo is listed
        run_cmd(
            'yum repolist enabled | grep {}'.format(base_repo_name),
            retcodes=[1]
        )

        # dry run check
        api_call(
            'set_swupdate_repo',
            release,
            source=source,
            dry_run=True
        )
        #   verify that nothing has changed in the system
        check_not_installed(release, expected_repo_name, mount_dir)
        # check no any update repo is listed
        run_cmd(
            'yum repolist enabled | grep {}'.format(base_repo_name),
            retcodes=[1]
        )

    # two repos concurrently
    for release, source, expected_rpm_name in [
        ('1.2.5', repo_dir, prvsnr_pkg_name),
        ('1.2.6', iso_path, prvsnr_pkg_name),
        ('1.2.7', repo_dir, prvsnr_pkg_name),
        ('1.2.8', iso_path, prvsnr_pkg_name)
    ]:
        expected_repo_name = '{}_{}'.format(base_repo_name, release)

        if source is iso_path:
            mount_dir = Path(pillar_params['base_dir']) / release
        else:
            mount_dir = None

        # INSTALL
        api_call(
            'set_swupdate_repo', release, source=source
        )

        # check repo is enabled
        run_cmd(
            'yum repolist enabled | grep {}'.format(expected_repo_name)
        )

    res = run_cmd(
        'yum repolist enabled | grep {}'.format(base_repo_name)
    )
    for _id, _res in res.items():
        assert len(_res['ret'].strip().split(os.linesep)) == 4

    for release, source, expected_rpm_name in [
        ('1.2.5', repo_dir, prvsnr_pkg_name),
        ('1.2.6', iso_path, prvsnr_pkg_name),
        ('1.2.7', repo_dir, prvsnr_pkg_name),
        ('1.2.8', iso_path, prvsnr_pkg_name)
    ]:

        expected_repo_name = '{}_{}'.format(base_repo_name, release)

        if source is iso_path:
            mount_dir = Path(pillar_params['base_dir']) / release
        else:
            mount_dir = None

        if api_type in ('py', 'pycli'):
            from provisioner import UNDEFINED
            undefined_value = UNDEFINED
        else:
            undefined_value = 'PRVSNR_UNDEFINED'

        # REMOVE
        # TODO UNDEFINED
        api_call(
            'set_swupdate_repo',
            release,
            source=undefined_value
        )
        check_not_installed(release, expected_repo_name, mount_dir)

    run_cmd(
        'yum repolist enabled | grep {}'.format(base_repo_name),
        retcodes=[1]
    )


def test_set_swupdate_repo_for_reinstall():
    repo_dir = os.environ['TEST_REPO_DIR']
    test_file_path = os.environ['TEST_FILE_PATH']
    # base_repo_name = 'cortx_update'
    prvsnr_pkg_name = 'cortx-prvsnr'

    release = '1.2.3'
    source = repo_dir
    # expected_rpm_name = prvsnr_pkg_name

    # INSTALL
    api_call(
        'set_swupdate_repo', release, source=source, targets=minion_id
    )

    run_cmd(
        "yum reinstall {}".format(prvsnr_pkg_name)
    )

    from provisioner.config import PRVSNR_ROOT_DIR
    assert (PRVSNR_ROOT_DIR / test_file_path).exists()


# TODO for now just tests that repo is installed and yum able
#      to start installation (which will definitely fail)
#   - install CORTX stack first from some release
#   - set some newer release
#   - call udpate
# FIXME: We would need an input from RE team, whether a release repo will be public or not.
# If not - we will make that thing optional so the test can be run inside Seagate network only.
# def test_cortx_update():
#     api_call(
#         'set_swupdate_repo',
#         '1.2.3',
#         source='http://<cortx_release_server>/releases/cortx/integration/centos-7.7.1908/last_successful',  # noqa: E501
#         targets=minion_id
#     )

#     api_call('cortx_update', targets=minion_id)
