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

from typing import Dict, List
import logging
import functools


from .config import ALL_MINIONS
from .errors import ProvisionerError
from .salt import runner_function_run, StatesApplier, function_run
from .utils import ensure

logger = logging.getLogger(__name__)


# TODO TEST
# case 1: config_salt_minions raises if no active minions found
# case 2: minions up check succeeds for both cases (restart happened or not)
# case 3: logic fails if minion config is malformed


# TODO TEST
def list_minions():
    # TODO optimize timeouts
    res = runner_function_run(
        'manage.up', fun_kwargs=dict(
            timeout=1, gather_job_timeout=1
        )
    )
    return list(res)


# TODO TEST
def check_salt_minions_are_ready(targets: List):
    ready = list_minions()
    return not (set(targets) - set(ready))


def ensure_salt_minions_are_ready(targets: List):
    ensure(
        functools.partial(check_salt_minions_are_ready, targets),
        tries=20, wait=30
    )

# FIXME
# 1) slat-minion might start even with malformed config
#   - ??? but sometimes fail


# TODO TEST
def check_salt_minions_restarted(pids: Dict):
    targets = list(pids)
    if check_salt_minions_are_ready(targets):
        _targets = ','.join(targets)
        res = function_run(
            'service.show', fun_args=('salt-minion',),
            targets=_targets, timeout=10, tgt_type='list'
        )
        _pids = {
            minion_id: _res['MainPID'] for minion_id, _res in res.items()
            if type(_res) is dict
        }
        return not (
            set(pids.items()) & set(_pids.items())
        )

    return False


def config_salt_minions(targets=ALL_MINIONS):
    logger.info("Updating salt-minion configuration")

    res = function_run(
        'service.show', fun_args=('salt-minion',),
        targets=targets, timeout=10
    )

    minions = list(res)

    if not minions:
        raise ProvisionerError('no minions found')

    pids = {
        minion_id: _res['MainPID'] for minion_id, _res in res.items()
        if type(_res) is dict
    }

    not_running = set(res) - set(pids)
    if len(not_running):
        raise ProvisionerError(f'{not_running} minions are not running')

    # apply new configuration
    res = StatesApplier.apply(
        ['provisioner.salt_minion.config'], targets
    )['provisioner.salt_minion.config']

    state_name = 'file_|-salt_minion_config_updated_|-/etc/salt/minion_|-managed'  # noqa: E501
    changes = {
        minion_id: _res[state_name]['changes']
        for minion_id, _res in res.items() if _res[state_name]['changes']
    }

    logger.info(
        'Minions have been configured with the changes: {}'.format(changes)
    )

    # if changes:
    #    ensure(
    #        functools.partial(check_salt_minions_restarted, pids),
    #        tries=10, wait=1
    #    )

    # Note. sync_all in a state doesn't work as expected even
    # following the salt docs
    # https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.saltutil.html#salt.modules.saltutil.sync_all
    function_run('saltutil.sync_all', targets=targets)
    return changes
