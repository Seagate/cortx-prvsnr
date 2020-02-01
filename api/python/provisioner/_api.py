from .errors import UnknownParamError
from .config import PRVSNR_USER_PILLAR_DIR
from .utils import load_yaml, dump_yaml
from .salt import (
    auth_init as _auth_init,
    pillar_get as _pillar_get,
    states_apply, pillar_refresh
)



# TODO
# - yaml file with
#   config param name | list of: <pillar filepath>-<pillar-key-path>-<value> | states to apply
# - cache of pillar files
# - logic of cache update (watchers ?)
# - async API
# - typing
#
# - rollback
# - action might require a set of preliminary steps - hard to describe using generic spec (yaml)

prvsnr_params = {
    'ntp_server': {
        'states': {
            'post': [
                'components.system.ntp.config',
                'components.system.ntp.stop',
                'components.system.ntp.start'
            ]
        },
        'pillar': {
            'key_path': ('system', 'ntp', 'time_server'),
            'path': 'system.sls',
        }
    },
    'ntp_timezone': {
        'states': {
            'post': [
                'components.system.ntp.config',
                'components.system.ntp.stop',
                'components.system.ntp.start'
            ]
        },
        'pillar': {
            'key_path': ('system', 'ntp', 'timezone'),
            'path': 'system.sls',
        }
    },
    'nw_primary_mgmt_ip': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-1', 'network', 'mgmt_nw', 'ipaddr'),
            'path': 'cluster.sls',
        }
    },
    'nw_primary_data_ip': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-1', 'network', 'data_nw', 'ipaddr'),
            'path': 'cluster.sls',
        }
    },
    'nw_slave_mgmt_ip': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-2', 'network', 'mgmt_nw', 'ipaddr'),
            'path': 'cluster.sls',
        }
    },
    'nw_slave_data_ip': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-2', 'network', 'data_nw', 'ipaddr'),
            'path': 'cluster.sls',
        }
    },
    'nw_primary_gateway_ip': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-1', 'network', 'gateway_ip'),
            'path': 'cluster.sls',
        }
    },
    'nw_slave_gateway_ip': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-2', 'network', 'gateway_ip'),
            'path': 'cluster.sls',
        }
    },
    'nw_primary_hostname': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-1', 'hostname'),
            'path': 'cluster.sls',
        }
    },
    'nw_slave_hostname': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            'key_path': ('cluster', 'eosnode-2', 'hostname'),
            'path': 'cluster.sls',
        }
    },
    'nw_dns_server': {
        'states': {
            'post': [
                # TODO network states to apply ???
                # 'components.system.network.config'
            ]
        },
        'pillar': {
            # TODO not supported in states
            #'key_path': ('cluster', 'eosnode-2', 'network', 'data_nw', 'ipaddr'),
            #'path': 'cluster.sls',
        }
    }
}



def auth_init(username, password, eauth='pam'):
    return _auth_init(username, password, eauth=eauth)


def pillar_get(targets='*'):
    return _pillar_get(targets=targets)


#  - Notes:
#       1. call salt pillar is good since salt will expand properly pillar itself
#       2. if pillar != system state then we are bad
#           - then assume they are in-sync
#  - ? what are cases when pillar != system
#  - ? options to check/ensure sync:
#     - salt.mine
#     - periodical states apply
def get_params(*params, targets='*'):
    res = {}
    key_paths = {}
    for param in params:
        if param not in prvsnr_params:
            raise UnknownParamError(param)
        key_paths[param] = prvsnr_params[param]['pillar']['key_path']

    if key_paths:
        pillar = pillar_get(targets=targets)
        # TODO provide results per target
        # - for now just use the first target's pillar value
        target, pillar_data = next(iter(pillar.items()))
        for param in params:
            key_path = key_paths[param]
            pillar_value = pillar_data
            for key in key_path:  # TODO optimize
                pillar_value = pillar_value[key]
            res[param] = pillar_value

    return res


# TODO
#   - how to support targetted pillar
#       - per group (grains)
#       - per minion
#       - ...
#   - !!! don't update installed pillar
#       - might be lost during the update
#       - mess things
#
#       - option:
#
#         pillar_roots:
#           base:
#             - /opt/seagate/eos-prvsnr/pillar/base
#           custom:
#             - /opt/seagate/eos-prvsnr/pillar/custom
#
def set_params(targets='*', **params):
    for param in params:
        if param not in prvsnr_params:
            raise UnknownParamError(param)

    # TODO
    # - class for pillar file
    # - caching (load once)
    # - one refresh
    # - rollback
    for param, value in params.items():
        spec = prvsnr_params[param]

        pillar = spec['pillar']
        pillar_path = PRVSNR_USER_PILLAR_DIR / pillar['path']
        pillar_data = load_yaml(pillar_path) if pillar_path.exists() else {}
        key_path = pillar['key_path']
        pillar_key = pillar_data

        for key in key_path[:-1]:  # TODO optimize
            # ensure key exists
            if key not in pillar_key:
                pillar_key[key] = {}
            pillar_key = pillar_key[key]

        pillar_key[key_path[-1]] = value

        if not pillar_path.exists():
            pillar_path.parent.mkdir(parents=True, exist_ok=True)
            pillar_path.touch()

        try:
            states = spec['states'].get('pre', [])
            if states:
                states_apply(states=states, targets=targets)

            dump_yaml(pillar_path, pillar_data)

            pillar_refresh(targets=targets)
        except Exception:
            # TODO rollback
            raise
        else:
            states = spec['states'].get('post', [])
            if states:
                states_apply(states=states, targets=targets)


def set_ntp(server=None, timezone=None, targets='*'):
    params = {}
    if server is not None:
        params['ntp_server'] = server
    if timezone is not None:
        params['ntp_timezone'] = timezone
    return set_params(**params)


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
    targets='*'
):
    params = {}
    if primary_mgmt_ip is not None:
        params['nw_primary_mgmt_ip'] = primary_mgmt_ip
    if primary_data_ip is not None:
        params['nw_primary_data_ip'] = primary_data_ip
    if slave_mgmt_ip is not None:
        params['nw_slave_mgmt_ip'] = slave_mgmt_ip
    if slave_data_ip is not None:
        params['nw_slave_data_ip'] = slave_data_ip
    if primary_gateway_ip is not None:
        params['nw_primary_gateway_ip'] = primary_gateway_ip
    if slave_gateway_ip is not None:
        params['nw_slave_gateway_ip'] = slave_gateway_ip
    if primary_hostname is not None:
        params['nw_primary_hostname'] = primary_hostname
    if slave_hostname is not None:
        params['nw_slave_hostname'] = slave_hostname
    if dns_server is not None:
        params['nw_dns_server'] = dns_server
    return set_params(**params)
