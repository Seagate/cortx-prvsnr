import importlib

from .config import ALL_MINIONS, CONTROLLER_BOTH

_api = None

api_types = {
    'py': 'provisioner._api',
    'pycli': 'provisioner._api_cli',
}

DEFAULT_API_TYPE = 'py'


def set_api(api_type=DEFAULT_API_TYPE):
    """Sets api engine.

    :param api_type (optional): might be either ``py`` or ``pycli``. The former
        is an ordinary python application that communicates directly with
        SaltStack using its API. The latter is a wrapper over provisioner cli
        and suitable to be used inside frozen python application.
    """

    global _api
    _api = importlib.import_module(api_types[api_type])


def _api_call(fun, *args, **kwargs):
    if _api is None:
        set_api()
    return getattr(_api, fun)(*args, **kwargs)


def auth_init(username, password, eauth='pam'):
    r"""Configures authentication credentials.

    To run provisioner commands using non-root user it is required
    to provide authentication credentials.

    :param username: Name of a user. The user should be a member of
        ``prvsnrusers`` group.
    :param password: The user's password.
    :param eauth: The user's password.
    :param eauth: An authentication scheme to use for a user authentication.
        Default is ``pam``. (*Note* the only option for now)
    """

    return _api_call('auth_init', username, password, eauth='pam')


def get_result(cmd_id: str):
    r"""Returns result of previously scheduled command

    :param cmd_id: Command id
    """

    return _api_call(
        'get_result', cmd_id
    )


def pillar_get(targets=ALL_MINIONS, nowait=False):
    return _api_call('pillar_get', targets=targets, nowait=nowait)


def get_params(*params, targets=ALL_MINIONS, nowait=False):
    return _api_call(
        'get_params', *params, targets=targets, nowait=nowait
    )


def set_params(targets=ALL_MINIONS, dry_run=False, **params):
    return _api_call('set_params', targets=targets, dry_run=dry_run, **params)


def set_ntp(
    server=None, timezone=None, targets=ALL_MINIONS,
    dry_run=False, nowait=False
):
    r"""Configures NTP client.

    :param server: (optional) NTP server domain or IP address.
    :param timezone: (optional) Host time zone.
    :param targets: (optional) Host targets. Default: ``ALL_MINIONS``
    :param nowait: (optional) Run asynchronously. Default: False

    Example:
    .. highlight:: python
    .. code-block:: python

        from provisioner import set_ntp

        new_ntp_server = '0.north-america.pool.ntp.org'
        new_ntp_timezone = 'Europe/Berlin'

        set_ntp(server=new_ntp_server, timezone=new_ntp_timezone)

    """

    return _api_call(
        'set_ntp', server=server, timezone=timezone,
        targets=targets, dry_run=dry_run, nowait=nowait
    )


def set_network(dry_run=False, nowait=False, **kwargs):
    r"""Configures network.

    :param cluster_ip: (optional) cluster ip address for public data network
    :param mgmt_vip: (optional) virtual ip address for management network
    :param dns_servers: (optional) list of dns servers
    :param search_domains: (optional) list of search domains
    :param primary_hostname: (optional) primary node hostname
    :param primary_floating_ip: (optional) primary node floating ip address
    :param primary_mgmt_ip: (optional) primary node management iface ip address
    :param primary_mgmt_netmask: (optional) primary node management
        iface netmask
    :param primary_mgmt_gateway: (optional) primary node gateway ip address
    :param primary_data_ip: (optional) primary node data iface ip address
    :param primary_data_netmask: (optional) primary node data iface netmask
    :param primary_data_gateway: (optional) primary node data iface gateway
    :param secondary_hostname: (optional) secondary node hostname
    :param secondary_floating_ip: (optional) secondary node floating ip address
    :param secondary_mgmt_ip: (optional) secondary node management
        iface ip address
    :param secondary_mgmt_netmask: (optional) secondary node management
        iface netmask
    :param secondary_mgmt_gateway: (optional) secondary node gateway ip address
    :param secondary_data_ip: (optional) secondary node data iface ip address
    :param secondary_data_netmask: (optional) secondary node data iface netmask
    :param secondary_data_gateway: (optional) secondary node data iface gateway
    :param dry_run: (optional) validate only. Default: False
    :param nowait: (optional) Run asynchronously. Default: False
    """
    # TODO better targettng: apply for nodes which need to be updated
    targets = kwargs.pop('targets', ALL_MINIONS)
    if targets != ALL_MINIONS:
        raise ValueError(
            'targets should be ALL_MINIONS, provided: {}'.format(targets)
        )
    return _api_call(
        'set_network', targets=targets,
        dry_run=dry_run, nowait=nowait, **kwargs
    )


# def set_cluster_ip(cluster_ip, dry_run=False, nowait=False):
#     r"""Configures network.

#     :param cluster_ip: cluster ip address for public data network
#     :param dry_run: (optional) validate only. Default: False
#     :param nowait: (optional) Run asynchronously. Default: False
#     """
#     # TODO better targettng: apply for nodes which need to be updated
#     return _api_call(
#         'set_cluster_ip', cluster_ip,
#         targets=LOCAL_MINION, dry_run=dry_run, nowait=nowait
#     )


# def set_mgmt_vip(mgmt_vip, dry_run=False, nowait=False):
#     r"""Configures network.

#     :param mgmt_vip: virtual ip address for management network
#     :param dry_run: (optional) validate only. Default: False
#     :param nowait: (optional) Run asynchronously. Default: False
#     """
#     # TODO better targettng: apply for nodes which need to be updated
#     return _api_call(
#         'set_mgmt_vip', mgmt_vip,
#         targets=LOCAL_MINION, dry_run=dry_run, nowait=nowait
#     )


def set_eosupdate_repo(
    release, source=None, targets=ALL_MINIONS, dry_run=False, nowait=False
):
    r"""Configures update repository.

    Installs or removes a repository for EOS update release.

    :param release: An update repository release label
    :param targets: Host where to install repos
    :param source: (optional) A path to a repository. Might be: a local
        directory,  a local iso file or an url to a remote repository.
        If not specified then a repository for a ``release`` will be removed.
        If path to an iso file is provide then it is mounted before
        installation and unmounted before removal.
    :param dry_run: (optional) validate only. Default: False
    :param nowait: (optional) Run asynchronously. Default: False
    """
    return _api_call(
        'set_eosupdate_repo',
        release, source=source, targets=targets, dry_run=dry_run, nowait=nowait
    )


def set_ssl_certs(
    source, restart=False, dry_run=False, nowait=True
):
    r"""Configures ssl certs

    Installs or removes a repository for EOS update release.

    :param source: (optional) A path to pem file. Might be: a local
    :param restart: switch to restart services
    :param nowait: (optional) Run asynchronously. Default: False
    """
    return _api_call(
        'set_ssl_certs',
        source, restart=restart, dry_run=dry_run, nowait=nowait
    )


def eos_update(targets=ALL_MINIONS, nowait=False):
    r"""Runs EOS software update logic.

    Updates EOS components one by one.

    :param targets: (optional) A host to update. Default: all minions
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'eos_update', targets=targets, nowait=nowait
    )


def fw_update(source, dry_run=False, nowait=False):
    r"""Runs EOS firmware update logic.

    :param source: A path to a new firmware
    :param dry_run: (optional) validate only. Default: False
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'fw_update', source, dry_run=dry_run, nowait=nowait
    )


def get_cluster_id(nowait=False):
    r"""Retruns cluster ID

    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'get_cluster_id', nowait=nowait
    )


def get_node_id(targets=ALL_MINIONS, nowait=False):
    r"""Retruns node ID

    :param targets: (optional) A host to find node ID.
        Default: ``ALL_MINIONS``
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'get_node_id', targets=targets, nowait=nowait
    )


def reboot_server(targets=ALL_MINIONS, nowait=False):
    r"""Reboots the servers

    :param targets: (optional) A host to shutdown. Default: all minions
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'reboot_server', targets=targets, nowait=nowait
    )


def reboot_controller(target_ctrl=CONTROLLER_BOTH, nowait=False):
    r"""Reboot the controller.

    :param target_ctrl: (optional) controller to reboot. Default: both
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'reboot_controller', target_ctrl=target_ctrl, nowait=nowait
    )


def shutdown_controller(target_ctrl=CONTROLLER_BOTH, nowait=False):
    r"""Shutdown the controller.

    :param target_ctrl: (optional) controller to reboot. Default: both
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'shutdown_controller', target_ctrl=target_ctrl, nowait=nowait
    )


def configure_eos(
    component, source=None, show=False, reset=False, nowait=False
):
    r"""Reboots the servers

    Updates or resolves configuration for specified EOS component
    depending on passed arguments:
      - if ``source`` is True then returns current component's pillar
      - if ``reset`` is True than reset the component's pillar to default state
      - otherwise ``source`` should be specified and will be set as a pillar
        for the component

    :param component: EOS component to configure
    :param source: (optional) A yaml file to apply. Default: None
    :param show: (optional) Dump current configuration. Default: False
    :param reset: (optional) Reset configuration to the factory state
        to default state. Default: False
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'configure_eos', component, source=source, show=show, reset=reset
    )
