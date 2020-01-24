import os
import logging
import pytest

from provisioner.errors import ProvisionerError, SaltError
from provisioner.salt import pillar_get, auth_init
from provisioner import get_params, set_ntp, set_network

logger = logging.getLogger(__name__)


def test_ntp_configuration():
    pillar = pillar_get()

    pillar_ntp_server = pillar['eosnode-1']['system']['ntp']['time_server']
    pillar_ntp_timezone = pillar['eosnode-1']['system']['ntp']['timezone']

    try:
        curr_params = get_params('ntp_server', 'ntp_timezone')
    except ProvisionerError:
        raise

    api_ntp_server = curr_params['ntp_server']
    api_ntp_timezone = curr_params['ntp_timezone']
    assert pillar_ntp_server == api_ntp_server
    assert pillar_ntp_timezone == api_ntp_timezone

    new_ntp_server = '0.north-america.pool.ntp.org'
    new_ntp_timezone = 'Europe/Berlin'

    try:
        set_ntp(server=new_ntp_server, timezone=new_ntp_timezone)
    except ProvisionerError:
        raise

    try:
        curr_params = get_params('ntp_server', 'ntp_timezone')
    except ProvisionerError:
        raise

    api_ntp_server = curr_params['ntp_server']
    api_ntp_timezone = curr_params['ntp_timezone']
    assert new_ntp_server == api_ntp_server
    assert new_ntp_timezone == api_ntp_timezone


# TODO slave params
def test_network_configuration():
    pillar = pillar_get()

    pillar_nw_primary_mgmt_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['mgmt_nw']['ipaddr']
    pillar_nw_primary_data_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['data_nw']['ipaddr']
    pillar_nw_primary_gateway_ip = pillar['eosnode-1']['cluster']['eosnode-1']['network']['gateway_ip']
    pillar_nw_primary_hostname = pillar['eosnode-1']['cluster']['eosnode-1']['hostname']

    api_nw_primary_mgmt_ip = get_params('nw_primary_mgmt_ip')['nw_primary_mgmt_ip']
    assert pillar_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = get_params('nw_primary_data_ip')['nw_primary_data_ip']
    assert pillar_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = get_params('nw_primary_gateway_ip')['nw_primary_gateway_ip']
    assert pillar_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = get_params('nw_primary_hostname')['nw_primary_hostname']
    assert pillar_nw_primary_hostname == api_nw_primary_hostname

    # TODO what values is bettwe to use here ???
    new_nw_primary_mgmt_ip = '192.168.7.7'
    new_nw_primary_data_ip = '192.168.7.8'
    new_nw_primary_gateway_ip = '192.168.7.9'
    new_nw_primary_hostname = 'new-hostname'

    set_network(
        primary_mgmt_ip=new_nw_primary_mgmt_ip,
        primary_data_ip=new_nw_primary_data_ip,
        primary_gateway_ip=new_nw_primary_gateway_ip,
        primary_hostname=new_nw_primary_hostname,
    )

    api_nw_primary_mgmt_ip = get_params('nw_primary_mgmt_ip')['nw_primary_mgmt_ip']
    assert new_nw_primary_mgmt_ip == api_nw_primary_mgmt_ip

    api_nw_primary_data_ip = get_params('nw_primary_data_ip')['nw_primary_data_ip']
    assert new_nw_primary_data_ip == api_nw_primary_data_ip

    api_nw_primary_gateway_ip = get_params('nw_primary_gateway_ip')['nw_primary_gateway_ip']
    assert new_nw_primary_gateway_ip == api_nw_primary_gateway_ip

    api_nw_primary_hostname = get_params('nw_primary_hostname')['nw_primary_hostname']
    assert new_nw_primary_hostname == api_nw_primary_hostname


def test_external_auth():
    username = os.environ['TEST_USERNAME']
    password = os.environ['TEST_PASSWORD']
    expected_exc = os.environ.get('TEST_ERROR')

    if username:
        auth_init(username=username, password=password)

    if expected_exc is None:
        pillar_get()
    else:
        with pytest.raises(SaltError) as excinfo:
            pillar_get()
        assert expected_exc in str(excinfo)
