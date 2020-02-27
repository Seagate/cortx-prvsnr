import attr
from salt.client import LocalClient
from typing import List, Union, Dict
import logging

from .config import ALL_MINIONS
from .errors import SaltError

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


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


# TODO tests
@attr.s(auto_attribs=True, frozen=True)
class State:
    name: str = attr.ib(converter=str)

    def __str__(self):
        return self.name


def _salt_client_cmd(*args, **kwargs):
    if _username or 'username' in kwargs:
        kwargs['eauth'] = kwargs.get('eauth', _eauth)
        kwargs['username'] = kwargs.get('username', _username)
        kwargs['password'] = kwargs.get('password', _password)

    try:
        res = LocalClient().cmd(*args, full_return=True, **kwargs)
    except Exception as exc:
        # TODO too generic
        raise SaltError(repr(exc)) from exc

    if not res:
        raise SaltError('salt returned nothing')

    # TODO is it a valid case actually ?
    if type(res) is not dict:
        return res

    results = {}
    fails = {}
    for target, job_result in res.items():
        ret = job_result['ret']
        results[target] = ret

        _fails = {}
        if job_result['retcode'] != 0:
            salt_fun = args[1]
            if str(salt_fun).startswith('state.') and type(ret) is dict:
                for task, tresult in ret.items():
                    if not tresult['result']:
                        _fails[task] = tresult['comment']
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
def function_run(fun, *args, targets=ALL_MINIONS, **kwargs):

    return _salt_client_cmd(targets, fun, list(args), **kwargs)


# TODO test
def cmd_run(cmd, targets=ALL_MINIONS):
    logger.info(
        "Running command '{}' on '{}'".format(
            cmd, targets
        )
    )
    res = function_run('cmd.run', cmd, targets=targets)
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
            res = function_run('state.apply', state.name, targets=targets)
            logger.info(
                "Applied state {} on {}, res {}".format(
                    state, targets, res
                )
            )
        except SaltError:
            raise
        except Exception as exc:
            raise SaltError(
                "Failed to apply state '{}': {}"
                .format(state, str(exc))
            )
        else:
            ret[state.name] = res

    return ret


# TODO tests
@attr.s(auto_attribs=True)
class StatesApplier:
    @staticmethod
    def apply(states: List[State], targets: str = ALL_MINIONS) -> None:
        if states:
            return states_apply(states=states, targets=targets)


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

        if not len(self.last_txn_ids):
            raise ValueError(
                "No targets matched for '{}'"
                .format(self.targets)
            )
        elif (
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
                "yum history rollback {}".format(txn_id),
                targets=target
            )
            logger.info("Rollback on target {} is completed".format(target))

    @property
    def last_txn_ids(self):
        return self._last_txn_ids
