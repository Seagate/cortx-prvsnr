import importlib
import logging
import sys 
import logging.handlers

from .config import ALL_MINIONS

_api = None

api_types = {
    'py': 'provisioner._api',
    'pycli': 'provisioner._api_cli',
}

DEFAULT_API_TYPE = 'py'

logger = logging.getLogger(__name__)

DEF_LOGGING_FORMAT = ("%(asctime)s - %(name)s - %(levelname)s - "
                      "[%(filename)s:%(lineno)d]: %(message)s")
DEF_LOGLEVEL = 'DEBUG'

root = logging.getLogger()
root.setLevel(0)
handler = logging.handlers.SysLogHandler(facility='local1')
handler.setLevel(DEF_LOGLEVEL)
handler.setFormatter(logging.Formatter(DEF_LOGGING_FORMAT))
root.addHandler(handler)

def set_api(api_type=DEFAULT_API_TYPE):
    """Sets api engine.

    :param api_type (optional): might be either ``py`` or ``pycli``. The former
        is an ordinary python application that communicates directly with
        SaltStack using its API. The latter is a wrapper over provisioner cli
        and suitable to be used inside frozen python application.
    """

    global _api
    logger.info("Requesting to set API type to {}..".format(api_type))
    _api = importlib.import_module(api_types[api_type])
    logger.info("API type successfully set to {}".format(api_type))


def _api_call(fun, *args, **kwargs):
    if _api is None:
        logger.warning("API type is not set!!")
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
    logger.info("Requesting to authenticate {} user..")
    res=_api_call('auth_init', username, password, eauth='pam')
    logger.info("Authentication successful!! {}".format(res))


def pillar_get(targets=ALL_MINIONS):
    logger.info("Requesting pillar data of *..")
    res=_api_call('pillar_get', targets=targets)
    logger.info("Response pillar data: \n {}".format(res))
    return res

def get_params(*params, targets=ALL_MINIONS):
    logger.info("Requesting {} params data of *..".format(*params))
    res=_api_call(
        'get_params', *params, targets=targets
    )
    logger.info("Response params data: \n {}".format(res))
    return res


def set_params(targets=ALL_MINIONS, dry_run=False, **params):
    logger.info("Requesting to set {} params for *..".format(*params))
    res=_api_call('set_params', targets=targets, dry_run=dry_run, **params)
    logger.info("Response params data: \n {}".format(res))
    return res


def set_ntp(server=None, timezone=None, targets=ALL_MINIONS, dry_run=False):
    r"""Configures NTP client.

    :param server: (optional) NTP server domain or IP address.
    :param timezone: (optional) Host time zone.
    :param targets: (optional) Host targets. Default: ``ALL_MINIONS``

    Example:
    .. highlight:: python
    .. code-block:: python

        from provisioner import set_ntp

        new_ntp_server = '0.north-america.pool.ntp.org'
        new_ntp_timezone = 'Europe/Berlin'

        set_ntp(server=new_ntp_server, timezone=new_ntp_timezone)

    """
    logger.info("Requesting to configure NTP with {} time server and {} timezone..".format(server,timezone))
    res=_api_call(
        'set_ntp', server=server, timezone=timezone,
        targets=targets, dry_run=dry_run
    )
    logger.info("Response time data: \n {}".format(res))
    return res


def set_network(dry_run=False, **kwargs):
    r"""Configures network.

    :param primary_hostname: (optional) primary node hostname
    :param primary_floating_ip: (optional) primary node floating ip address
    :param primary_gateway_ip: (optional) primary node gateway ip address
    :param primary_mgmt_ip: (optional) primary node management iface ip address
    :param primary_mgmt_netmask: (optional) primary node management
        iface netmask
    :param primary_data_ip: (optional) primary node data iface ip address
    :param primary_data_netmask: (optional) primary node data iface netmask
    :param slave_hostname: (optional) slave node hostname
    :param slave_floating_ip: (optional) slave node floating ip address
    :param slave_gateway_ip: (optional) slave node gateway ip address
    :param slave_mgmt_ip: (optional) slave node management iface ip address
    :param slave_mgmt_netmask: (optional) slave node management iface netmask
    :param slave_data_ip: (optional) slave node data iface ip address
    :param slave_data_netmask: (optional) slave node data iface netmask
    :param dry_run: (optional) validate only
    """
    # TODO better targettng: apply for nodes which need to be updated
    targets = kwargs.pop('targets', ALL_MINIONS)
    logger.info("Requesting to configure the network..")
    if targets != ALL_MINIONS:
        logger.error("ValueError: targets should be ALL_MINIONS, provided: {}".format(targets))
        #raise ValueError(
        #    'targets should be ALL_MINIONS, provided: {}'.format(targets)
        #)
    res=_api_call('set_network', **kwargs, targets=targets, dry_run=dry_run)
    logger.info("Response network configuration: \n {}".format(res))
    return res


def set_eosupdate_repo(
    release, source=None, targets=ALL_MINIONS, dry_run=False
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
    """
    logger.info("Requesting to update eos repository with {}..".format(release))
    res=_api_call(
        'set_eosupdate_repo',
        release, source=source, targets=targets, dry_run=dry_run
    )
    logger.info("Response EOSUpdateRepo: \n {}".format(res))
    return res


def eos_update(targets=ALL_MINIONS):
    r"""Runs EOS software update logic.

    Updates EOS components one by one.

    :param targets: A host to update.
    """
    logger.info("Requesting to update EOS stack..")
    res=_api_call(
        'eos_update', targets=targets
    )
    logger.info("Response from EOSUpdate: \n {}".format(res))
