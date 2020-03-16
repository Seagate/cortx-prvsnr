import attr
import salt.config
from salt.client import LocalClient, Caller
from typing import List, Union, Dict, Tuple
import logging

from .config import ALL_MINIONS, LOCAL_MINION
from .errors import SaltError, SaltEmptyReturnError

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


_salt_local_client = None
_salt_caller = None
_local_minion_id = None


def username():
    return _username


def password():
    return _password


def eauth():
    return _eauth


def salt_local_client():
    global _salt_local_client
    if not _salt_local_client:
        _salt_local_client = LocalClient()
    return _salt_local_client


def salt_caller():
    global _salt_caller
    if not _salt_caller:
        _salt_caller = Caller()
    return _salt_caller


def local_minion_id():
    global _local_minion_id

    if not _local_minion_id:
        __opts__ = salt.config.minion_config('/etc/salt/minion')
        __opts__['file_client'] = 'local'
        caller = Caller(mopts=__opts__)
        _local_minion_id = caller.cmd('grains.get', 'id')
        if not _local_minion_id:
            raise SaltError('Failed to get local minion id')

    return _local_minion_id


# TODO
#   - think about static salt client (one for the module)
def auth_init(username, password, eauth='pam'):
    global _eauth
    global _username
    global _password
    _eauth = eauth
    _username = username
    _password = password


# salt full return format (TODO ??? salt docs for that)
"""
{
    '<target>': {
        'jid': '<jid>',
        'out': '<output-format>',
        'ret': {
            '<task-id-key>': {
                '__id__': '<task-string-id>'
                '__run_num__': 1,
                '__sls__': '<state-path-dotted>',
                'changes': {<changes dict>},
                'comment': '<human-readable-comment>',
                'duration': 37.465,
                ...
                'result': True,
                'start_time': '13:34:30.645186'
            },
            ...
        },
        'retcode': 0
    }
}
"""

# RunnerClient.cmd('jobs.print_job', ('20200312210442593007',), full_return=True, print_event=False) # noqa E501
# TODO
#   - ??? salt docs for that)
#   - ??? how to get separate stderr and stdout
"""
IN PROGRESS

{
    "fun": "runner.jobs.print_job",
    "jid": "20200312210508420587",
    "user": "UNKNOWN",
    "fun_args": [
        "20200312210442593007"
    ],
    "_stamp": "2020-03-12T21:05:08.616156",
    "return": {
        "20200312210442593007": {
            "Function": "cmd.run",
            "Arguments": [
                "sleep 30 && echo 123 && ls 123"
            ],
            "Target": "eosnode-1",
            "Target-type": "glob",
            "User": "root",
            "Minions": [
                "eosnode-1"
            ],
            "StartTime": "2020, Mar 12 21:04:42.593007",
            "Result": {}
        }
    },
    "success": true
}

FINISHED

{
    "fun": "runner.jobs.print_job",
    "jid": "20200312205806533552",
    "user": "UNKNOWN",
    "fun_args": [
        "20200312204750664984"
    ],
    "_stamp": "2020-03-12T20:58:06.760168",
    "return": {
        "20200312204750664984": {
            "Function": "cmd.run",
            "Arguments": [
                "sleep 30 && echo 123 && ls 123"
            ],
            "Target": "eosnode-1",
            "Target-type": "glob",
            "User": "root",
            "Minions": [
                "eosnode-1"
            ],
            "StartTime": "2020, Mar 12 20:47:50.664984",
            "Result": {
                "eosnode-1": {
                    "return": "123\nls: cannot access 123: No such file or directory", # noqa E501
                    "retcode": 2,
                    "success": false
                }
            }
        }
    },
    "success": true
}

ERROR CASE (bad jid)

{
    "fun": "runner.jobs.print_job",
    "jid": "20200312210108994035",
    "user": "UNKNOWN",
    "fun_args": [
        2020031220475066498
    ],
    "_stamp": "2020-03-12T21:01:09.224500",
    "return": {
        "2020031220475066498": {
            "Error": "Cannot contact returner or no job with this jid",
            "StartTime": "",
            "Result": {}
        }
    },
    "success": true
}
"""


# TODO tests
@attr.s(auto_attribs=True, frozen=True)
class State:
    name: str = attr.ib(converter=str)

    def __str__(self):
        return self.name


# TODO tests
@attr.s(auto_attribs=True, frozen=True)
class StateFun:
    name: str = attr.ib(converter=str)

    def __str__(self):
        return self.name


# TODO tests
def _get_fails(ret: Dict):
    fails = {}
    for task, tresult in ret.items():
        if not tresult['result']:
            fails[task] = tresult['comment']
    return fails


# TODO tests
def _salt_caller_cmd(*args, **kwargs):
    # XXX salt's Caller doesn't support external_auth
    #     and should be run under the same user as a minion
    #     https://docs.saltstack.com/en/latest/ref/clients/#salt.client.Caller
    if _username or 'username' in kwargs:
        kwargs['eauth'] = kwargs.get('eauth', _eauth)
        kwargs['username'] = kwargs.get('username', _username)
        kwargs['password'] = kwargs.get('password', _password)

    try:
        # TODO
        #  - consider to use --local arg to reduce
        #    unnecessary connections with master
        res = salt_caller().cmd(*args, full_return=True, **kwargs)
    except Exception as exc:
        # TODO too generic
        raise SaltError(repr(exc)) from exc

    if not res:
        raise SaltEmptyReturnError

    # TODO is it a valid case actually ?
    if type(res) is dict:
        fails = _get_fails(res)

        if fails:
            # TODO better logging
            # TODO add res to exception data
            raise SaltError(
                "salt command failed: {}".format(fails)
            )

    return res


def _salt_client_cmd(
    targets, fun,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    nowait=False,
    **kwargs
):
    def _repr_inputs():
        return (
            'targets: {}, fun: {}, fun_args: {}, fun_kwargs: {}, kwargs: {}'
            .format(targets, fun, fun_args, fun_kwargs, kwargs)
        )

    eauth = kwargs.pop('eauth', _eauth)
    username = kwargs.pop('username', _username)
    password = kwargs.pop('password', _password)

    if not fun_args:
        fun_args = ()

    if username:
        kwargs['eauth'] = eauth
        kwargs['username'] = username
        kwargs['password'] = password

    kwargs['full_return'] = True
    try:
        if kwargs.pop('async', False):
            res = salt_local_client().cmd_async(
                targets, fun, arg=fun_args,
                kwarg=fun_kwargs, **kwargs
            )
            if res == 0:
                raise SaltError(
                    'Async API returned 0, inputs: {}'
                    .format(_repr_inputs())
                )
        else:
            res = salt_local_client().cmd(
                targets, fun, arg=fun_args,
                kwarg=fun_kwargs, **kwargs
            )
    except Exception as exc:
        # TODO too generic
        raise SaltError(repr(exc)) from exc

    if not res:
        raise SaltEmptyReturnError

    # TODO is it a valid case actually ?
    if type(res) is not dict:
        return res

    results = {}
    fails = {}
    for target, job_result in res.items():
        ret = job_result.get('ret') if type(job_result) is dict else None

        if ret is None:
            results[target] = job_result
            continue
        else:
            results[target] = ret

        _fails = {}
        if job_result.get('retcode') != 0:
            salt_fun = fun
            if str(salt_fun).startswith('state.') and type(ret) is dict:
                _fails = _get_fails(ret)
            else:
                _fails = ret

        if _fails:
            fails[target] = _fails

    if fails:
        # TODO better logging
        # TODO add res to exception data
        raise SaltError(
            "salt command failed: {}".format(fails)
        )

    return results


def pillar_get(targets=ALL_MINIONS):
    return _salt_client_cmd(targets, 'pillar.items')


def pillar_refresh(targets=ALL_MINIONS):
    return _salt_client_cmd(targets, 'saltutil.refresh_pillar')


# TODO test
def function_run(
    fun,
    targets=ALL_MINIONS,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    **kwargs
):
    if targets == LOCAL_MINION:
        targets = local_minion_id()

    # XXX Caller for local minion commands works not smoothly,
    #     issues with ioloop, possibly related one
    #     https://github.com/saltstack/salt/issues/46905
    # return _salt_caller_cmd(fun, *args, **kwargs)

    return _salt_client_cmd(
        targets, fun, fun_args=fun_args, fun_kwargs=fun_kwargs, **kwargs
    )


# TODO test
def cmd_run(cmd, targets=ALL_MINIONS):
    logger.info(
        "Running command '{}' on '{}'".format(
            cmd, targets
        )
    )
    res = function_run('cmd.run', fun_args=[cmd], targets=targets)
    logger.info(
        "Run command '{}' on '{}', res {}".format(
            cmd, targets, res
        )
    )
    return res


def states_apply(states: List[Union[str, State]], targets=ALL_MINIONS):
    ret = {}

    # TODO multiple states at once
    for state in states:
        state = State(state)
        try:
            logger.info(
                "Applying state {} on {}".format(
                    state, targets
                )
            )
            res = function_run(
                'state.apply', fun_args=[state.name], targets=targets
            )
            logger.info(
                "Applied state {} on {}, res {}".format(
                    state, targets, res
                )
            )
        except Exception as exc:
            raise SaltError(
                "Failed to apply state '{}': {}"
                .format(state, str(exc))
            )
        else:
            ret[state.name] = res

    return ret


# TODO tests
def state_fun_execute(
    state_fun: Union[str, StateFun],
    targets: str = LOCAL_MINION,
    fun_args: Union[List, Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    **kwargs
):
    # TODO multiple states at once
    state_fun = StateFun(state_fun)
    try:
        logger.info(
            "Executing state function {} on {}".format(
                state_fun, targets
            )
        )
        if not fun_args:
            fun_args = ()
        res = function_run(
            'state.single',
            targets=targets,
            fun_args=[state_fun.name] + list(fun_args),
            fun_kwargs=fun_kwargs,
            **kwargs
        )
        logger.info(
            "Executed state function {} on {}, res {}".format(
                state_fun, targets, res
            )
        )
    except Exception as exc:
        raise SaltError(
            "Failed to execute state function '{}': {}"
            .format(state_fun, str(exc))
        )
    else:
        return res


# TODO tests
@attr.s(auto_attribs=True)
class StatesApplier:
    @staticmethod
    def apply(states: List[State], targets: str = ALL_MINIONS) -> None:
        if states:
            return states_apply(states=states, targets=targets)


# TODO tests
@attr.s(auto_attribs=True)
class StateFunExecuter:
    @staticmethod
    def execute(
        fun: str,
        targets: str = LOCAL_MINION,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        **kwargs
    ) -> None:
        return state_fun_execute(
            fun,
            targets=targets,
            fun_args=fun_args,
            fun_kwargs=fun_kwargs,
            **kwargs
        )


# TODO test
@attr.s(auto_attribs=True)
class YumRollbackManager:
    targets: str = ALL_MINIONS
    multiple_targets_ok: bool = False
    _last_txn_ids: Dict = attr.ib(init=False, default=attr.Factory(dict))

    def __enter__(self):
        self._last_txn_ids = cmd_run(
            "yum history | head -n 4 | tail -n1 | awk '{print $1}'",
            targets=self.targets
        )

        if (
            not self.multiple_targets_ok
            and (len(self.last_txn_ids) > 1)
        ):
            raise ValueError(
                "Multiple targetting is not expected, "
                "matched targets: {} for '{}'"
                .format(list(self.last_txn_ids), self.targets)
            )

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return

        for target, txn_id in self._last_txn_ids.items():
            logger.info("Starting rollback on target {}".format(target))
            cmd_run(
                "yum history rollback -y {}".format(txn_id),
                targets=target
            )
            logger.info("Rollback on target {} is completed".format(target))

    @property
    def last_txn_ids(self):
        return self._last_txn_ids
