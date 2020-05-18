import functools

from .salt import runner_function_run
from .utils import ensure
from .errors import SaltCmdRunError
import logging

logger = logging.getLogger(__name__)


# TODO TEST:
# case 1: (hard to make reproducible)
#   - changes in config
#   - master is being restarted
#   - some runner check is failed due to connection to previous master
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
            res['ActiveState'] == 'active'
            and res['SubState'] == 'running'
            and res['MainPID'] != pid_before
        )


def config_salt_master():
    # get salt master PID
    res = runner_function_run(
        'salt.cmd', fun_args=('service.show', 'salt-master')
    )
    pid = res['MainPID']

    # apply new configuration
    res = runner_function_run(
        'salt.cmd',
        fun_args=('state.apply', 'components.provisioner.salt_master.config')
    )
    state_name = 'file_|-salt_master_config_updated_|-/etc/salt/master_|-managed'  # noqa: E501
    changes = res[state_name]['changes']

    # XXX might be moved to rollback part
    # on configuration changes - expect salt master is going to be restarted
    if changes:
        ensure(
            functools.partial(check_salt_master_is_restarted, pid),
            tries=30, wait=1
        )


def ensure_salt_master_is_running():
    runner_function_run(
        'salt.cmd', fun_args=('state.single', 'service.running', 'salt-master')
    )
