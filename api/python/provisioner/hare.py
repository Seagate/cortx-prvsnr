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

import logging
import os
from datetime import datetime
from pathlib import Path

from .config import LOCAL_MINION, ALL_MINIONS, PRVSNR_ROOT_DIR
from .salt import cmd_run, StatesApplier
from .utils import ensure
from . import errors

try:
    # TODO: what is the correct import path?
    from cortx.hare import CortxClusterManager
except ImportError:
    CortxClusterManager = None


logger = logging.getLogger(__name__)


def consul_export(fn_suffix='', no_fail=True, targets=ALL_MINIONS):
    # TODO move to configuration routine
    dest_dir = Path('/var/lib/hare/prvsnr_generated')
    consul_legacy = Path('/usr/bin/consul')

    ts = datetime.now().strftime("%Y%m%dT%H.%M.%S")
    pid = os.getpid()
    out_file = (dest_dir / f'consul-kv.{ts}.{fn_suffix}.{pid}.json')

    def _export_consul(consul='consul'):
        return cmd_run(
            f"mkdir -p {dest_dir} && {consul} kv export >{out_file}",
            fun_kwargs=dict(python_shell=True)
        )

    try:
        try:
            logger.debug("Exporting consul kv store")
            return _export_consul()
        except errors.SaltCmdResultError as exc:
            if 'consul: command not found' in str(exc):
                logger.warning(
                    f"No 'consul' found in PATH, fallback to {consul_legacy}, "
                    f"error: {exc}"
                )
                return _export_consul(consul_legacy)
            else:
                raise
    except Exception:
        if no_fail:
            logger.exception('Consul export failed')
        else:
            raise


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

    res = cmd_run(
        ' '.join(cmd),
        targets=LOCAL_MINION,
        background=background,
        timeout=(timeout + 60)
    )
    return next(iter(res.values()))


def cluster_maintenance_enable(**kwargs):
    logger.info("Enabling cluster maintenance mode")
    return cluster_maintenance(True, **kwargs)


def cluster_maintenance_disable(**kwargs):
    logger.info("Disabling cluster maintenance mode")
    return cluster_maintenance(False, **kwargs)


# TODO TEST EOS-8940
def apply_ha_post_update(targets=ALL_MINIONS):
    logger.info(f"Applying Hare post_update logic on {targets}")
    return StatesApplier.apply(
        ["components.ha.iostack-ha.post_update"],
        targets
    )


# TODO IMPROVE may lead to errors for stpopped cluster like:
#      "Error: cluster is not currently running on this node"
def check_cluster_is_offline():
    ret = cluster_status()
    return ('OFFLINE:' in ret)


# TODO TEST EOS-8940
def check_cluster_is_online():
    for path in (
        'cli/common_utils/utility_scripts.sh',
        'cli/src/common_utils/utility_scripts.sh'
    ):
        if (PRVSNR_ROOT_DIR / path).exists():
            utility_scripts = PRVSNR_ROOT_DIR / path
            break
    else:
        raise RuntimeError('Utility scripts are not found')

    res = cmd_run(
        (
            f"bash -c "
            f"'. {utility_scripts}; ensure_healthy_cluster false'"
        ),
        targets=LOCAL_MINION
    )
    return next(iter(res.values()))


def ensure_cluster_is_stopped(tries=30, wait=1):
    cluster_stop()
    # no additional checks are needed since
    # cluster stop is a sync operation


def ensure_cluster_is_started(tries=30, wait=10):
    cluster_start()
    ensure(check_cluster_is_online, tries=tries, wait=wait)


# TODO IMPROVE EOS-8940 currently we rely on utility_scripts.sh as it
#      has its own looping logic, so only one try here
def ensure_cluster_is_healthy(tries=1, wait=10):
    logger.info("Ensuring cluster is online and healthy")
    ensure(check_cluster_is_online, tries=tries, wait=wait)


def r2_check_cluster_health_status() -> bool:
    """
    Wrapper over API of the hare which provides the capability to check
    the health status of cluster.

    Returns
    -------
    bool
        True if the health status check of the cluster succeeds and
        False otherwise

    """
    # ret = cluster_status()
    # return 'OFFLINE:' in ret
    cm = CortxClusterManager()
    try:
        res = cm.cluster_controller.status()
    except Exception as e:
        logger.debug(f"Some Hare exception occurred: {e}")
        return False
    else:
        # TODO: we need to parse the output
        if not res:
            return False

        return True
