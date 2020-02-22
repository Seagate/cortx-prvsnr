import importlib

from .config import ALL_MINIONS

_api = None

api_types = {
    'py': 'provisioner._api',
    'pycli': 'provisioner._api_cli',
}

DEFAULT_API_TYPE = 'py'


def set_api(api_type=DEFAULT_API_TYPE):
    global _api
    _api = importlib.import_module(api_types[api_type])


def _api_call(fun, *args, **kwargs):
    if _api is None:
        set_api()
    return getattr(_api, fun)(*args, **kwargs)


def auth_init(username, password, eauth='pam'):
    return _api_call('auth_init', username, password, eauth=eauth)


def pillar_get(targets=ALL_MINIONS):
    return _api_call('pillar_get', targets=targets)


def get_params(*params, targets=ALL_MINIONS):
    return _api_call(
        'get_params', *params, targets=targets
    )


def set_params(targets=ALL_MINIONS, **params):
    return _api_call('set_params', targets=targets, **params)


def set_ntp(server=None, timezone=None, targets=ALL_MINIONS):
    return _api_call(
        'set_ntp', server=server, timezone=timezone, targets=targets
    )


def set_network(
    primary_mgmt_ip=None,
    primary_data_ip=None,
    slave_mgmt_ip=None,
    slave_data_ip=None,
    primary_gateway_ip=None,
    slave_gateway_ip=None,
    primary_hostname=None,
    slave_hostname=None,
    dns_server=None,
    targets=ALL_MINIONS
):
    return _api_call(
        'set_network',
        primary_mgmt_ip=primary_mgmt_ip,
        primary_data_ip=primary_data_ip,
        slave_mgmt_ip=slave_mgmt_ip,
        slave_data_ip=slave_data_ip,
        primary_gateway_ip=primary_gateway_ip,
        slave_gateway_ip=slave_gateway_ip,
        primary_hostname=primary_hostname,
        slave_hostname=slave_hostname,
        dns_server=dns_server,
        targets=targets
    )


def set_eosupdate_repo(release, targets, source=None):
    return _api_call(
        'set_eosupdate_repo',
        release, source=source, targets=targets
    )


def eos_update(targets):
    return _api_call(
        'eos_update', targets=targets
    )
