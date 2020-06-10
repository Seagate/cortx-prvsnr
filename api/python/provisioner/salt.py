import attr
import salt.config
from salt.client import LocalClient, Caller
from salt.runner import RunnerClient
from typing import List, Union, Dict, Tuple, Iterable, Any
from pathlib import Path
import logging

from .config import (
   ALL_MINIONS, LOCAL_MINION,
   PRVSNR_USER_FILEROOTS_DIR
)
from .errors import (
    ProvisionerError,
    SaltError, SaltNoReturnError,
    SaltCmdRunError, SaltCmdResultError,
    PrvsnrCmdNotFinishedError, PrvsnrCmdNotFoundError
)
from .values import is_special
from ._api_cli import process_cli_result

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


_salt_local_client = None
_salt_runner_client = None
_salt_caller = None
_salt_caller_local = None
_local_minion_id = None


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

# TODO check default values
@attr.s(auto_attribs=True)
class SaltJob:
    _prvsnr_type_ = True

    jid: str
    error: str = ''
    function: str = ''
    arguments: List = attr.Factory(list)
    target: str = ''
    target_type: str = ''
    user: str = ''
    minions: List = attr.Factory(list)
    starttime: str = ''
    result: Dict = attr.Factory(dict)

    @classmethod
    def from_salt_res(cls, jid: str, data: Dict):
        data = {k.lower().replace('-', '_'): v for k, v in data.items()}
        return cls(jid, **data)

    @property
    def is_failed(self):
        return not self.error  # FIXME


# TODO TEST
@attr.s(auto_attribs=True)
class SaltArgsMixin:
    @property
    def args(self):
        return (self.fun,)

    @property
    def kwargs(self):
        return dict(arg=self.fun_args, kwarg=self.fun_kwargs, **self.kw)

    def __str__(self):
        _dct = attr.asdict(self)
        if 'password' in _dct['kw']:
            _dct['kw']['password'] = '*' * 7

        _self_safe = type(self)(**_dct)
        return str(attr.asdict(_self_safe))


# TODO TEST
@attr.s(auto_attribs=True)
class SaltRunnerArgs(SaltArgsMixin):
    _prvsnr_type_ = True

    fun: str = attr.ib(converter=str)
    fun_args: Tuple = attr.ib(
        converter=lambda v: () if v is None else v, default=None
    )
    fun_kwargs: Dict = attr.ib(
        converter=lambda v: {} if v is None else v, default=None
    )
    nowait: bool = False
    kw: Dict = attr.Factory(dict)


# TODO TEST
@attr.s(auto_attribs=True)
class SaltRunnerResult:
    _prvsnr_type_ = True

    jid: str
    fun: str
    success: bool
    result: Any
    stamp: str = ''
    user: str = ''
    fun_args: List = attr.Factory(list)

    @classmethod
    def from_salt_res(cls, data: Dict):
        _data = {
            k.lower().replace('-', '_').lstrip('_'): v for k, v in data.items()
            if k != 'return'
        }
        if 'return' in data:
            _data['result'] = data['return']
        return cls(**_data)


# TODO TEST
@attr.s(auto_attribs=True)
class SaltClientArgs(SaltArgsMixin):
    _prvsnr_type_ = True

    targets: str = attr.ib(converter=str)
    fun: str = attr.ib(converter=str)
    fun_args: Tuple = attr.ib(
        converter=lambda v: () if v is None else v, default=None
    )
    fun_kwargs: Dict = attr.ib(
        converter=lambda v: {} if v is None else v, default=None
    )
    nowait: bool = False
    kw: Dict = attr.Factory(dict)

    @property
    def args(self):
        return (self.targets, self.fun)


# TODO TYPE
# TODO TEST
@attr.s(auto_attribs=True)
class SaltClientResult:
    _prvsnr_type_ = True

    raw: Any
    cmd_args: SaltClientArgs
    results: Any = attr.ib(init=False, default=attr.Factory(dict))
    fails: Any = attr.ib(init=False, default=attr.Factory(dict))

    def __attrs_post_init__(self):
        # TODO is it a valid case actually ?
        if type(self.raw) is not dict:
            self.results = self.raw
            return

        # TODO HARDEN check format of result
        for target, job_result in self.raw.items():
            ret = None
            if type(job_result) is dict:
                # result format as a part of job differs (async result) from
                # sync case:
                #   - 'ret' for sync
                #   - 'return' for async
                ret = job_result.get('ret', job_result.get('return'))

            if ret is None:
                self.results[target] = job_result
                continue
            else:
                self.results[target] = ret

            _fails = {}
            if job_result.get('retcode') != 0:
                if (
                    self.cmd_args.fun.startswith('state.')
                    and (type(ret) is dict)
                ):
                    _fails = self._get_state_fails(ret)
                else:
                    _fails = ret

            if _fails:
                self.fails[target] = _fails

        # TODO TESTS
    def _get_state_fails(self, ret: Dict):
        fails = {}
        for task, tresult in ret.items():
            if not tresult['result']:
                fails[task] = {
                    'comment': tresult.get('comment'),
                    'changes': tresult.get('changes')
                }
        return fails


def username():
    return _username


def password():
    return _password


def eauth():
    return _eauth


def salt_local_client():
    global _salt_local_client
    # TODO IMPROVE in case of minion retsart old handler will
    #      lead to Authentication error, so always recreate it
    #      as a workaround for now
    if not _salt_local_client or True:
        _salt_local_client = LocalClient()
    return _salt_local_client


def salt_runner_client():
    global _salt_runner_client
    if not _salt_runner_client:
        __opts__ = salt.config.client_config('/etc/salt/master')
        _salt_runner_client = RunnerClient(opts=__opts__)
    return _salt_runner_client


def salt_caller():
    global _salt_caller
    if not _salt_caller:
        __opts__ = salt.config.minion_config('/etc/salt/minion')
        _salt_caller = Caller(mopts=__opts__)
    return _salt_caller


def salt_caller_local():
    global _salt_caller_local
    if not _salt_caller_local:
        __opts__ = salt.config.minion_config('/etc/salt/minion')
        __opts__['file_client'] = 'local'
        _salt_caller_local = Caller(mopts=__opts__)
    return _salt_caller_local


def local_minion_id():
    global _local_minion_id
    if not _local_minion_id:
        _local_minion_id = salt_caller_local().cmd('grains.get', 'id')
        if not _local_minion_id:
            logger.error("Failed to get local minion id")
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


# TODO TEST
def _set_auth(kwargs):
    eauth = kwargs.pop('eauth', _eauth)
    username = kwargs.pop('username', _username)
    password = kwargs.pop('password', _password)

    if username:
        kwargs['eauth'] = eauth
        kwargs['username'] = username
        kwargs['password'] = password

    return


def _salt_runner_cmd(
    fun: str,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    nowait=False,
    **kwargs
):
    # TODO FEATURE not yet supported
    if nowait:
        raise NotImplementedError(
            'async calls for RunnerClient are not supported yet'
        )

    # TODO log username / password ??? / eauth
    cmd_args = SaltRunnerArgs(
        fun, fun_args, fun_kwargs, nowait, kwargs
    )

    _set_auth(cmd_args.kw)

    eauth = 'username' in cmd_args.kw
    if not eauth:
        if nowait:
            raise NotImplementedError(
                'async calls without external auth for RunnerClient'
                ' are not supported yet'
            )
        cmd_args.kw['print_event'] = False
        cmd_args.kw['full_return'] = True

    try:
        if eauth:
            _cmd_f = (
                salt_runner_client().cmd_async if nowait
                else salt_runner_client().cmd_sync
            )
            low = dict(fun=fun, **cmd_args.kwargs)
            salt_res = _cmd_f(low, full_return=True)
        else:
            _cmd_f = salt_runner_client().cmd
            salt_res = _cmd_f(*cmd_args.args, **cmd_args.kwargs)
    except Exception as exc:
        raise SaltCmdRunError(cmd_args, exc) from exc

    if not salt_res:
        raise SaltNoReturnError(
            cmd_args, 'Empty salt result: {}'.format(salt_res)
        )

    if type(salt_res) is not dict:
        raise SaltCmdRunError(
            cmd_args, (
                'RunnerClient result type is not a dictionary: {}'
                .format(type(salt_res))
            )
        )

    if nowait:
        return salt_res

    if eauth:
        if 'data' not in salt_res:
            raise SaltCmdRunError(
                cmd_args, (
                    'no data key in RunnerClient result dictionary: {}'
                    .format(salt_res)
                )
            )
        res = salt_res['data']
    else:
        res = salt_res

    try:
        res = SaltRunnerResult.from_salt_res(res)
    except TypeError:
        msg = 'Failed to parse salt runner result: {}'.format(salt_res)
        logger.exception(msg)
        raise SaltCmdRunError(cmd_args, msg)

    if res.success:
        return res.result
    else:
        raise SaltCmdResultError(cmd_args, res.result)


# TODO TEST
# TODO DRY
def runner_function_run(
    fun,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    **kwargs
):
    logger.info(
        "Running runner function '{}', fun_args: {},"
        " fun_kwargs: {}, kwargs: {}"
        .format(
            fun, fun_args, fun_kwargs, kwargs
        )
    )

    try:
        res = _salt_runner_cmd(
            fun, fun_args=fun_args, fun_kwargs=fun_kwargs, **kwargs
        )
    except Exception:
        logger.exception("Salt runner command failed")
        raise

    logger.info(
        "Runner function '{}' resulted in {}".format(
            fun, res
        )
    )

    return res


# TODO LOGGING better logging coverage
def _salt_client_cmd(
    targets: str,
    fun: str,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    nowait=False,
    **kwargs
):
    # TODO log username / password ??? / eauth
    cmd_args = SaltClientArgs(
        targets, fun, fun_args, fun_kwargs, nowait, kwargs
    )

    _set_auth(cmd_args.kw)
    cmd_args.kw['full_return'] = True

    try:
        _cmd_f = (
            salt_local_client().cmd_async if nowait
            else salt_local_client().cmd
        )
        salt_res = _cmd_f(*cmd_args.args, **cmd_args.kwargs)
    except Exception as exc:
        # TODO too generic
        raise SaltCmdRunError(cmd_args, exc) from exc

    if not salt_res:
        reason = (
            'Async API returned empty result: {}'.format(salt_res) if nowait
            else 'Empty salt result: {}'.format(salt_res)
        )
        raise SaltNoReturnError(cmd_args, reason)

    if nowait:
        return salt_res

    res = SaltClientResult(salt_res, cmd_args)

    if res.fails:
        raise SaltCmdResultError(cmd_args, res.fails)
    else:
        return res.results


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

    logger.info(
        "Running function '{}' on '{}', fun_args: {},"
        " fun_kwargs: {}, kwargs: {}"
        .format(
            fun, targets, fun_args, fun_kwargs, kwargs
        )
    )

    try:
        res = _salt_client_cmd(
            targets, fun, fun_args=fun_args, fun_kwargs=fun_kwargs, **kwargs
        )
    except Exception:
        logger.exception("Salt client command failed")
        raise

    logger.info(
        "Function '{}' on '{}' resulted in {}".format(
            fun, targets, res
        )
    )

    return res


def pillar_get(targets=ALL_MINIONS):
    return function_run('pillar.items', targets=targets)


def pillar_refresh(targets=ALL_MINIONS):
    return function_run('saltutil.refresh_pillar', targets=targets)


# TODO test
def cmd_run(cmd, targets=ALL_MINIONS, background=False, timeout=None):
    return function_run(
        'cmd.run',
        fun_args=[cmd],
        fun_kwargs=dict(bg=background),
        targets=targets,
        timeout=timeout
    )


# TODO TEST
def process_provisioner_cmd_res(res):
    if not isinstance(res, dict):
        raise ProvisionerError(
            'Expected a dictionary, provided: {}, {}'
            .format(type(res), res)
        )

    _local_minion_id = local_minion_id()
    if _local_minion_id not in res:
        raise ProvisionerError(
            'local minion id {} is not in the results: {}'
            .format(_local_minion_id, res)
        )

    # provisioner cli output
    prvsnr_res = res[_local_minion_id]
    return process_cli_result(prvsnr_res)


def provisioner_cmd(
    cmd,
    fun_args: Union[List, Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    nowait=False,
    **kwargs
):
    _local_minion_id = local_minion_id()

    def _value(v):
        return str(v) if is_special(v) else v

    _fun_args = fun_args
    if isinstance(fun_args, Iterable):
        _fun_args = [_value(v) for v in fun_args]

    _fun_kwargs = fun_kwargs
    if isinstance(fun_kwargs, Dict):
        _fun_kwargs = {k: _value(v) for k, v in fun_kwargs.items()}

    try:
        res = function_run(
            'provisioner.{}'.format(cmd),
            fun_args=_fun_args,
            fun_kwargs=_fun_kwargs,
            targets=_local_minion_id,
            nowait=nowait,
            **kwargs
        )
    except SaltCmdResultError as exc:
        if nowait:
            raise ProvisionerError(
                'SaltClientResult is unexpected here: {!r}'.format(exc)
            ) from exc
        else:
            return process_provisioner_cmd_res(exc.reason)
    else:
        if nowait:
            return res
        else:
            return process_provisioner_cmd_res(res)


def states_apply(states: List[Union[str, State]], targets=ALL_MINIONS):
    # TODO multiple states at once
    ret = {}
    for state in states:
        state = State(state)
        res = function_run(
            'state.apply', fun_args=[state.name], targets=targets
        )
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
    kwargs['nowait'] = False  # TODO can it be needed ???
    state_fun = StateFun(state_fun)
    # TODO multiple states at once
    return function_run(
        'state.single',
        targets=targets,
        fun_args=[state_fun.name] + list(fun_args or []),
        fun_kwargs=fun_kwargs,
        **kwargs
    )


# TODO TEST
def copy_to_file_roots(source: Union[str, Path], dest: Union[str, Path]):
    source = Path(str(source))
    dest = PRVSNR_USER_FILEROOTS_DIR / dest

    if not source.exists():
        raise ValueError('{} not found'.format(source))

    if source.is_dir():
        # TODO
        #  - file.recurse expects only dirs from maste file roots
        #    (salt://), need to find another alternative to respect
        #    indempotence
        # StateFunExecuter.execute(
        #     'file.recurse',
        #     fun_kwargs=dict(
        #       source=str(params.source),
        #       name=str(dest)
        #     )
        # )
        StateFunExecuter.execute(
            'cmd.run',
            fun_kwargs=dict(
                name=(
                    "mkdir -p {0} && rm -rf {2} && cp -R {1} {2}"
                    .format(dest.parent, source, dest)
                )
            )
        )
    else:
        StateFunExecuter.execute(
            'file.managed',
            fun_kwargs=dict(
                source=str(source),
                name=str(dest),
                makedirs=True
            )
        )

    # ensure it would be visible for Salt master / minions
    runner_function_run(
        'fileserver.clear_file_list_cache',
        fun_kwargs=dict(backend='roots')
    )


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


# TODO TEST
@attr.s(auto_attribs=True)
class SaltJobsRunner:

    @staticmethod
    def runner_function_run(*args, **kwargs):
        res = runner_function_run(*args, **kwargs)
        if type(res) is not dict:
            raise SaltError('not a dict result: {}'.format(res))
        return res

    @staticmethod
    def print_job(jid):
        res = SaltJobsRunner.runner_function_run(
            'jobs.print_job', fun_args=[jid]
        )
        return SaltJob.from_salt_res(*next(iter(res.items())))

    @staticmethod
    def list_jobs(search_function=None):
        res = SaltJobsRunner.runner_function_run(
            'jobs.list_jobs', fun_kwargs=dict(search_function=search_function)
        )
        return {
            jid: SaltJob.from_salt_res(jid, jid_data)
            for jid, jid_data in res.items()
        }

    @staticmethod
    def provisioner_jobs(fun: str = '*'):
        return SaltJobsRunner.list_jobs(
            search_function='provisioner.{}'.format(fun)
        )

    @classmethod
    def prvsnr_job_result(cls, jid):
        jobs = cls.provisioner_jobs()
        if jid in jobs:
            job = cls.print_job(jid)
            if not job.result:
                raise PrvsnrCmdNotFinishedError(jid)
            else:
                cmd_args = SaltClientArgs(
                    targets=job.minions,  # TODO ??? or job.target
                    fun=job.function,
                    fun_args=job.arguments
                )
                client_res = SaltClientResult(job.result, cmd_args)
                return process_provisioner_cmd_res(client_res.results)
        else:
            raise PrvsnrCmdNotFoundError(jid)


# TODO test
@attr.s(auto_attribs=True)
class YumRollbackManager:
    targets: str = ALL_MINIONS
    multiple_targets_ok: bool = False
    _last_txn_ids: Dict = attr.ib(init=False, default=attr.Factory(dict))
    _rollback_error: Union[Exception, None] = attr.ib(init=False, default=None)

    def __enter__(self):
        self._last_txn_ids = cmd_run(
            "yum history | grep ID -A 2 | tail -n1 | awk '{print $1}'",
            targets=self.targets
        )

        if (
            not self.multiple_targets_ok
            and (len(self.last_txn_ids) > 1)
        ):
            logger.error(
                "Multiple targetting is not expected, "
                "matched targets: {} for '{}'"
                .format(list(self.last_txn_ids), self.targets)
            )
            raise ValueError(
                "Multiple targetting is not expected, "
                "matched targets: {} for '{}'"
                .format(list(self.last_txn_ids), self.targets)
            )

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return

        try:
            # TODO IMPROVE minion might be stopped at that moment,
            #      option - use some ssh fallback
            for target, txn_id in self._last_txn_ids.items():
                logger.info("Starting rollback on target {}".format(target))
                cmd_run(
                    "yum history rollback -y {}".format(txn_id),
                    targets=target
                )
                logger.info(
                    "Rollback on target {} is completed".format(target)
                )
        except Exception as exc:
            self._rollback_error = exc

    @property
    def last_txn_ids(self):
        return self._last_txn_ids

    @property
    def rollback_error(self):
        return self._rollback_error


# SALT RESULT FORMATS

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

#   - ??? salt docs for that)
#   - ??? how to get separate stderr and stdout
"""
IN PROGRESS

{
    "return": {
        "20200312210442593007": {
            "Function": "cmd.run",
            "Arguments": [
                "sleep 30 && echo 123 && ls 123"
            ],
            "Target": "srvnode-1",
            "Target-type": "glob",
            "User": "root",
            "Minions": [
                "srvnode-1"
            ],
            "StartTime": "2020, Mar 12 21:04:42.593007",
            "Result": {}
        }
    },
    "success": true
}

FINISHED

{
    "return": {
        "20200312204750664984": {
            "Function": "cmd.run",
            "Arguments": [
                "sleep 30 && echo 123 && ls 123"
            ],
            "Target": "srvnode-1",
            "Target-type": "glob",
            "User": "root",
            "Minions": [
                "srvnode-1"
            ],
            "StartTime": "2020, Mar 12 20:47:50.664984",
            "Result": {
                "srvnode-1": {
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
    "return": {
        "2020031220475066498": {
            "Error": "Cannot contact returner or no job with this jid",
            "StartTime": "",
            "Result": {}
        }
    },
    "success": true
}


>>> res  =aaa.cmd('salt.cmd', 'provisioner.get_params', arg=('aaa',))
"""


# DRAFTS

# Expected result formats of salt clients XXX where is it documented?
# TODO REIMPLEMENT
'''
EXPECTED_RESULT_FORMATS = {
    'runner': {
        ('jid', str),
        ('_stamp', str),
        ('user', str),
        ('fun', str),
        ('fun_args', list),
        ('success', bool),
        ('return', ???) depends on command
    }
}
'''


'''
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
        raise SaltNoReturnError

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
'''
