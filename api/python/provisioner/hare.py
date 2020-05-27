import logging

from .config import LOCAL_MINION
from .salt import cmd_run
from .utils import ensure

logger = logging.getLogger(__name__)


def cluster_status():
    res = cmd_run('pcs status', targets=LOCAL_MINION)
    return next(iter(res.values()))


def cluster_stop():
    res = cmd_run('pcs cluster stop --all', targets=LOCAL_MINION)
    return next(iter(res.values()))


def cluster_start():
    res = cmd_run('pcs cluster start --all', targets=LOCAL_MINION)
    return next(iter(res.values()))


def cluster_maintenance(
    enable: bool, timeout: int = 600, verbose: bool = False, background=False
):
    cmd = [
        'hctl node',
        'maintenance' if enable else 'unmaintenance',
        '--all',
        '--timeout-sec={}'.format(timeout)
    ]

    if verbose:
        cmd.insert(1, '--verbose')

    res = cmd_run(' '.join(cmd), targets=LOCAL_MINION, background=background)
    return next(iter(res.values()))


def cluster_maintenance_enable(**kwargs):
    return cluster_maintenance(True, **kwargs)


def cluster_maintenance_disable(**kwargs):
    return cluster_maintenance(False, **kwargs)


# TODO IMPROVE may lead to errors for stpopped cluster like:
#      "Error: cluster is not currently running on this node"
def check_cluster_is_offline():
    ret = cluster_status()
    return ('OFFLINE:' in ret)


def check_cluster_is_online():
    ret = cluster_status()
    return ('Online:' in ret)


def ensure_cluster_is_stopped(tries=30, wait=1):
    cluster_stop()
    # no additional checks are needed since
    # cluster stop is a sync operation


def ensure_cluster_is_started(tries=30, wait=10):
    cluster_start()
    ensure(check_cluster_is_online, tries=tries, wait=wait)
