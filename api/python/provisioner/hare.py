#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging

from .config import LOCAL_MINION, ALL_MINIONS, PRVSNR_ROOT_DIR
from .salt import cmd_run, StatesApplier
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
    return StatesApplier.apply(["components.ha.ees_ha.post_update"], targets)


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
