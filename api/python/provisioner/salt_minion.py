from typing import Dict
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


# FIXME
# 1) slat-minion might start even with malformed config
#   - ??? but sometimes fail

def check_salt_minions_restarted(pids: Dict):
    targets = list(pids)
    _targets = ','.join(targets)
    # TODO IMPROVE in case of non-exitent minion
    #      salt will complain only to stdout and returns 0,
    #      so we won't get that, need better handling
    res = runner_function_run(
        'manage.up', fun_kwargs=dict(
            tgt=_targets, timeout=1, gather_job_timeout=1
        )
    )
    if set(targets) == set(res):
        res = function_run(
            'service.show', fun_args=('salt-minion',),
            targets=_targets, timeout=10
        )
        _pids = {minion_id: _res['MainPID'] for minion_id, _res in res.items()}
        return not (
            set(pids.items()) & set(_pids.items())
        )

    return False


def config_salt_minions(targets=ALL_MINIONS):
    res = function_run(
        'service.show', fun_args=('salt-minion',),
        targets=targets, timeout=10
    )
    pids = {minion_id: _res['MainPID'] for minion_id, _res in res.items()}

    minions = list(res)

    if not minions:
        raise ProvisionerError('no minions found')

    # apply new configuration
    res = StatesApplier.apply(
        ['components.provisioner.salt_minion.config'], targets
    )['components.provisioner.salt_minion.config']

    state_name = 'file_|-salt_minion_config_updated_|-/etc/salt/minion_|-managed'  # noqa: E501
    changes = {
        minion_id: _res[state_name]['changes']
        for minion_id, _res in res.items() if _res[state_name]['changes']
    }

    logger.info(
        'Minions has been configured with the changes: {}'.format(changes)
    )

    if changes:
        ensure(
            functools.partial(check_salt_minions_restarted, pids),
            tries=10, wait=1
        )

    # Note. sync_all in a state doesn't work as expected even following the salt docs
    # https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.saltutil.html#salt.modules.saltutil.sync_all
    function_run('saltutil.sync_all', targets=targets)
