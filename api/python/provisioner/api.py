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


def pillar_get(*keypaths, targets=ALL_MINIONS, nowait=False):
    return _api_call(
        'pillar_get', *keypaths, targets=targets, nowait=nowait
    )


def pillar_set(keypath, value, fpath=None, targets=ALL_MINIONS, nowait=False):
    return _api_call(
        'pillar_set', keypath, value, fpath=fpath,
        targets=targets, nowait=nowait
    )


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
    :param primary_roaming_ip: (optional) ip address for
        primary node roaming
    :param primary_mgmt_public_ip: (optional) ip address for
        primary node management interface
    :param primary_mgmt_netmask: (optional) netmask for
        primary node management interface
    :param primary_mgmt_gateway: (optional) gateway ip address for
        primary node
    :param primary_data_public_ip: (optional) ip address for
        primary node data interface
    :param primary_data_netmask: (optional) netmask for
        primary node data interface
    :param primary_data_gateway: (optional) gateway for
        primary node data interface
    :param secondary_hostname: (optional) secondary node hostname
    :param secondary_roaming_ip: (optional) ip address for
        secondary node roaming
    :param secondary_mgmt_public_ip: (optional) ip address for
        secondary node management interface
    :param secondary_mgmt_netmask: (optional) netmask for
        secondary node management interface
    :param secondary_mgmt_gateway: (optional) ip address for
        secondary node gateway
    :param secondary_data_public_ip: (optional) ip address for
        secondary node data interface
    :param secondary_data_netmask: (optional) netmask for
        secondary node data interface
    :param secondary_data_gateway: (optional) gateway for
        secondary node data interface
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


def set_swupdate_repo(
    release, source=None, targets=ALL_MINIONS, dry_run=False, nowait=False
):
    r"""Configures update repository.

    Installs or removes a repository for sw update release.

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
        'set_swupdate_repo',
        release, source=source, targets=targets, dry_run=dry_run, nowait=nowait
    )


def set_swupgrade_repo(release, source=None, dry_run=False, nowait=False):
    r"""Configures upgrade repository.

    Installs or removes a repository for sw upgrade release.

    Parameters
    ----------
    release
        An update repository release label
    source
        (optional) A path to a repository. Might be: a local
        directory,  a local iso file or an url to a remote repository.
        If not specified then a repository for a ``release`` will be removed.
        If path to an iso file is provide then it is mounted before
        installation and unmounted before removal.
    dry_run
        (optional) validate only. Default: False
    nowait
        (optional) Run asynchronously. Default: False

    Returns
    -------
    dict
        repository metadata

    """
    return _api_call('set_swupgrade_repo', release, source=source,
                     dry_run=dry_run, nowait=nowait)


def set_ssl_certs(
    source, restart=False, targets=ALL_MINIONS, dry_run=False, nowait=True
):
    r"""Configures ssl certs

    Installs or removes a repository for cortx update release.

    :param source: (optional) A path to pem file. Might be: a local
    :param restart: switch to restart services
    :param targets: (optional) A host (hosts) to install/update certificates.
           Default: all minions
    :param nowait: (optional) Run asynchronously. Default: False
    """
    return _api_call(
        'set_ssl_certs',
        source, restart=restart, targets=targets,
        dry_run=dry_run, nowait=nowait
    )


def sw_update(targets=ALL_MINIONS, nowait=False):
    r"""Runs software update logic.

    Updates components one by one.

    :param targets: (optional) A host to update. Default: all minions
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'sw_update', targets=targets, nowait=nowait
    )


def sw_upgrade(targets=ALL_MINIONS, nowait=False):
    """Runs software update logic.

    Updates components one by one.

    Parameters
    ----------
    targets:
        (optional) A host to update. Default: all minions
    nowait: bool
        (optional) Run asynchronously. Default: False

    Returns
    -------
    None

    """
    return _api_call('sw_upgrade', targets=targets, nowait=nowait)


def fw_update(source, dry_run=False, nowait=False):
    r"""Runs firmware update logic.

    :param source: A path to a new firmware
    :param dry_run: (optional) validate only. Default: False
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'fw_update', source, dry_run=dry_run, nowait=nowait
    )


def cmd_run(cmd_name: str, cmd_args: str = "", cmd_stdin: str = "",
            targets: str = ALL_MINIONS, nowait: bool = False,
            dry_run: bool = False):
    """
    Execute given command on targets nodes

    :param cmd_name: command to be executed
    :param cmd_args: (optional) commands' arguments
    :param cmd_stdin: (optional) commands stdin parameters like username or
                      password
    :param targets: (optional) target nodes for command execution
    :param nowait: (optional) Run asynchronously. Default: False
    :param dry_run: (optional) validate only.
    :return:
    """
    return _api_call('cmd_run', cmd_name, cmd_args=cmd_args,
                     cmd_stdin=cmd_stdin, targets=targets, nowait=nowait,
                     dry_run=dry_run)


def get_setup_info():
    """
    Get cluster setup information

    :return:
    """
    return _api_call("get_setup_info")


def get_cluster_id(nowait=False):
    r"""Returns cluster ID

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


def get_release_version(targets=ALL_MINIONS, nowait=False):
    r"""Retruns Release Version

    :param targets: (optional) A host to find Rlease Version.
        Default: ``ALL_MINIONS``
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'get_release_version', targets=targets, nowait=nowait
    )


def get_factory_version(targets=ALL_MINIONS, nowait=False):
    r"""Retruns Release Version

    :param targets: (optional) A host to find Rlease Version.
        Default: ``ALL_MINIONS``
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'get_factory_version', targets=targets, nowait=nowait
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


def configure_cortx(
    component, source=None, show=False, reset=False, nowait=False
):
    r"""Reboots the servers

    Updates or resolves configuration for specified component
    depending on passed arguments:
      - if ``source`` is True then returns current component's pillar
      - if ``reset`` is True than reset the component's pillar to default state
      - otherwise ``source`` should be specified and will be set as a pillar
        for the component

    :param component: CORTX component to configure
    :param source: (optional) A yaml file to apply. Default: None
    :param show: (optional) Dump current configuration. Default: False
    :param reset: (optional) Reset configuration to the factory state
        to default state. Default: False
    :param nowait: (optional) Run asynchronously. Default: False
    """

    return _api_call(
        'configure_cortx', component, source=source, show=show, reset=reset
    )


def replace_node(node_id, node_host=None, node_port=None, nowait=True):
    r"""Replace node. It will trigger replace node command and return job id

    :param node_id: node id of replacing node
    :param node_host: hostname of new node. Default: None
    :param node_port: ssh port of new node. Default: None
    :param nowait: (optional) Run asynchronously. Default: True
    """
    return _api_call(
        'replace_node',
        node_id=node_id, node_host=node_host,
        node_port=node_port, nowait=nowait
    )


def create_user(uname, passwd, targets=ALL_MINIONS, nowait=False):
    r"""Creates an user.

    :param uname: name of the user. Default: None
    :param passwd: password for the user. Default: None
    :param targets: (optional) targets to create user. Default: all minions
    :param nowait: (optional) Run asynchronously. Default: False
    """
    return _api_call(
        'create_user',
        uname, passwd, targets=targets, nowait=nowait
    )


def grains_get(*keys, targets=ALL_MINIONS, nowait=False):
    """
    Grains Get items provisioner API

    :param keys: grains keys to fetch data from the nodes
    :param targets: targets for grains data retrieving
    :param nowait: Run asynchronously. Default: False
    :param nowait: Run asynchronously. Default: False
    :return:
    """
    return _api_call('grains_get', *keys, targets=targets, nowait=nowait)


def check(check_name, check_args: str = "",
          targets: str = ALL_MINIONS):
    """
    Verify specific checks for system and beyond

    :param check_name: name of validation. Use `all` parameter to trigger all
                       supported checks
    :param check_args: arguments and parameters for check (if supported)
    :param targets: targets where to execute validations (optional)
    :return:
    """
    return _api_call('check', check_name,
                     check_args_args=check_args, targets=targets)
