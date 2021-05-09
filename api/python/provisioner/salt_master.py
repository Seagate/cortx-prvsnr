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

import functools
import time

from .salt import runner_function_run
from .salt_minion import (
    list_minions,
    ensure_salt_minions_are_ready
)
from .utils import ensure
from .errors import (
    SaltCmdRunError, SaltCmdResultError
)
import logging

logger = logging.getLogger(__name__)


# TODO TEST:
# case 1: (hard to make reproducible)
#   - changes in config
#   - salt-master is being restarted
#   - some runner check is failed due to connection to previous salt-master
#     ('Stream is closed')
# case 2: no restart checks happens if no changes detected
# case 3: logic fails if minion config is malformed
#
# TODO IMPROVE:
#   - if config is malformed runner commands will fail, thus rollback logic
#     will fail as well


def check_salt_master_is_restarted(pid_before):
    try:
        res = runner_function_run(
            'salt.cmd', fun_args=('service.show', 'salt-master')
        )
    except SaltCmdRunError as exc:
        if 'Stream is closed' in str(exc):
            logger.info(
                'salt-master connection error occured: {}'.format(exc)
            )
            return False
        else:
            raise
    else:
        # "ActiveState": "active",
        # "SubState": "running",
        return (
            res['ActiveState'] == 'active' and
            res['SubState'] == 'running' and
            res['MainPID'] != pid_before
        )


def check_salt_master_is_responded():
    try:
        # TODO IMPROVE ??? consider another function to run
        runner_function_run(
            'manage.status', fun_kwargs=dict(
                timeout=1, gather_job_timeout=1
            )
        )
    except SaltCmdResultError as exc:
        if ("Salt request timed out."
                "The salt-master is not responding") in str(exc):

            logger.info(
                'salt-master is not yet responding: {}'.format(exc)
            )
            return False
        else:
            raise
    else:
        return True


# TODO TEST
def config_salt_master():
    logger.info("Updating salt-master configuration")

    # get salt-master PID
    res = runner_function_run(
        'salt.cmd', fun_args=('service.show', 'salt-master')
    )
    pid = res['MainPID']

    up_minions = list_minions()

    # apply new configuration
    res = runner_function_run(
        'salt.cmd',
        fun_args=('state.apply', 'provisioner.salt_master.config')
    )
    state_name = 'file_|-salt_master_config_updated_|-/etc/salt/master_|-managed'  # noqa: E501
    changes = res[state_name]['changes']

    # XXX might be moved to rollback part
    # on configuration changes - expect salt-master is going to be restarted
    if changes:
        # TODO IMPROVE ??? better logic
        # small delay might help to avoid noise in the logs since
        # not responded yet salt-master will cause some excpetions which
        # we are going to suppress initially
        time.sleep(10)

        ensure(
            functools.partial(check_salt_master_is_restarted, pid),
            tries=30, wait=1
        )
        ensure(
            check_salt_master_is_responded,
            tries=30, wait=1
        )
        # ensure that minions reconnected
        # (keeping in mind that minion may try to reconnect only once
        # in a few minutes)
        # TODO IMPROVE make more dynamic based on actual minions configuration
        ensure_salt_minions_are_ready(up_minions)


def ensure_salt_master_is_running():
    logger.info("Ensuring salt-master is running")
    runner_function_run(
        'salt.cmd', fun_args=('state.single', 'service.running', 'salt-master')
    )
