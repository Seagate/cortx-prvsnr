import os
import logging
import pytest

api_type = os.environ['TEST_API_TYPE']
assert api_type in ('py', 'cli', 'pycli')

logger = logging.getLogger(__name__)


def api_call(fun, *args, **kwargs):
    if api_type in ('py', 'pycli'):
        import provisioner
        provisioner.set_api(api_type)
        return getattr(provisioner, fun)(*args, **kwargs)
    else:  # cli
        import subprocess
        import json

        _input = kwargs.pop('password', None)
        if _input is not None:
            kwargs['password'] = '-'

        kwargs['loglevel'] = 'DEBUG'
        kwargs['logstream'] = 'stderr'
        kwargs['output'] = 'json'

        cmd = ['provisioner', fun]
        for k, v in kwargs.items():
            cmd.extend(['--{}'.format(k), v])
        cmd.extend(list(args))
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

    curr_params = api_call('get_params', 'ntp_server', 'ntp_timezone')

    api_ntp_server = curr_params['ntp_server']
    api_ntp_timezone = curr_params['ntp_timezone']
    assert pillar_ntp_server == api_ntp_server
    assert pillar_ntp_timezone == api_ntp_timezone

    new_ntp_server = '0.north-america.pool.ntp.org'
    new_ntp_timezone = 'Europe/Berlin'

    api_call('set_ntp', server=new_ntp_server, timezone=new_ntp_timezone)

    curr_params = api_call('get_params', 'ntp_server', 'ntp_timezone')

    api_ntp_server = curr_params['ntp_server']
    api_ntp_timezone = curr_params['ntp_timezone']
    assert new_ntp_server == api_ntp_server
    assert new_ntp_timezone == api_ntp_timezone


# TODO slave params
def test_network_configuration():
    pillar = api_call('pillar_get')

    pillar_nw_primary_mgmt_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['mgmt_nw']['ipaddr']
    pillar_nw_primary_data_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['data_nw']['ipaddr']
    pillar_nw_primary_gateway_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['gateway_ip']
    pillar_nw_primary_hostname = pillar['eosnode-1']['cluster']['eosnode-1']['hostname']

    api_nw_primary_mgmt_ip = api_call('get_params', 'nw_primary_mgmt_ip')['nw_primary_mgmt_ip']
    assert pillar_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = api_call('get_params', 'nw_primary_data_ip')['nw_primary_data_ip']
    assert pillar_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = api_call('get_params', 'nw_primary_gateway_ip')['nw_primary_gateway_ip']
    assert pillar_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = api_call('get_params', 'nw_primary_hostname')['nw_primary_hostname']
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

    api_nw_primary_mgmt_ip = api_call('get_params', 'nw_primary_mgmt_ip')['nw_primary_mgmt_ip']
    assert new_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = api_call('get_params', 'nw_primary_data_ip')['nw_primary_data_ip']
    assert new_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = api_call('get_params', 'nw_primary_gateway_ip')['nw_primary_gateway_ip']
    assert new_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = api_call('get_params', 'nw_primary_hostname')['nw_primary_hostname']
    assert new_nw_primary_hostname == api_nw_primary_hostname
