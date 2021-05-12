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

from abc import ABC, abstractmethod
import salt.config
from salt.client import LocalClient, Caller
from salt.runner import RunnerClient
from typing import (
    List, Union, Dict, Tuple, Iterable, Any, Callable, Type, Optional
)
from salt.client.ssh.client import SSHClient
from pathlib import Path
import logging
from pprint import pformat

from .vendor import attr
from .config import (
   ALL_MINIONS, LOCAL_MINION,
   PRVSNR_USER_FILEROOT_DIR,
   SECRET_MASK
)
from .errors import (
    ProvisionerError,
    SaltError, SaltNoReturnError,
    SaltCmdRunError, SaltCmdResultError,
    PrvsnrCmdNotFinishedError, PrvsnrCmdNotFoundError
)
from .ssh import copy_id
from .values import is_special
from ._api_cli import process_cli_result
from .utils import load_yaml

logger = logging.getLogger(__name__)

_eauth = 'pam'
_username = None
_password = None


_salt_local_client = None
_salt_runner_client = None
_salt_caller = None
_salt_caller_local = None
_salt_ssh_client = None

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
        _dct = self._as_dict()
        _self_safe = type(self)(**_dct)
        return str(attr.asdict(_self_safe))

    def _as_dict(self):
        _dct = attr.asdict(self)
        if 'password' in _dct['kw']:
            _dct['kw']['password'] = SECRET_MASK

        if 'password' in _dct['fun_kwargs']:
            _dct['fun_kwargs']['password'] = SECRET_MASK

        # we do not mask the 'kw' more since
        # it should include only salt related parameters
        # that are safe to show
        if self.secure:
            _dct['fun_args'] = SECRET_MASK
            _dct['fun_kwargs'] = SECRET_MASK

        return _dct


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
    secure: bool = False


# TODO TEST
# TODO IMPROVE EOS-14361 optionally mask fun_args
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


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltClientArgsBase(SaltArgsMixin):
    _prvsnr_type_ = True

    targets: str = attr.ib(converter=str)
    fun: str = attr.ib(converter=str)
    fun_args: Tuple = attr.ib(
        converter=lambda v: () if v is None else v, default=None
    )
    fun_kwargs: Dict = attr.ib(
        converter=lambda v: {} if v is None else v, default=None
    )
    kw: Dict = attr.Factory(dict)
    secure: bool = False

    @property
    def args(self):
        return (self.targets, self.fun)


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltClientArgs(SaltClientArgsBase):
    nowait: bool = False


@attr.s(auto_attribs=True)
class SaltCallerArgs(SaltClientArgsBase):
    targets: Any = attr.ib(init=False, default=None)
    kw: Any = attr.ib(init=False, default=attr.Factory(dict))

    @property
    def args(self):
        return (self.fun, *self.fun_args)

    @property
    def kwargs(self):
        return self.fun_kwargs


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHArgs(SaltClientArgsBase):
    pass


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHResultBase(ABC):
    _prvsnr_type_ = True
    raw: Any
    # some not tracked fields
    other: Dict

    _result: Any = attr.ib(init=False, default=None)
    _fail: Any = attr.ib(init=False, default=None)

    @property
    def result(self):
        return self._result

    @property
    def fail(self):
        return self._fail


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHRawResult(SaltSSHResultBase):
    other: Dict = attr.ib(init=False, default=attr.Factory(dict))

    def __attrs_post_init__(self):
        self._result = self.raw


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHSimpleResult(SaltSSHResultBase):
    retcode: int
    stderr: str
    stdout: str

    def __attrs_post_init__(self):
        self._result = self.stdout
        if self.retcode:
            self._fail = f'STDERR: {self.stderr}, STDOUT: {self.stdout}'


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHJobResult(SaltSSHResultBase):
    retcode: int
    jid: str
    fun: str
    fun_args: List
    jresult: Any

    def __attrs_post_init__(self):
        self._result = self.jresult

        # TODO IMPROVE better error presentation
        if self.retcode or (
            type(self._result) is dict and
            self._result.get('retcode')
        ):
            self._fail = self._result


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHStateJobResult(SaltSSHJobResult):

    def __attrs_post_init__(self):
        self._result, _fail = self._get_state_results(self.jresult)
        if _fail:
            self._fail = _fail

    # TODO IMPROVE EOS-8473
    def _get_state_results(self, ret: Dict):
        results = {}
        fails = {}
        for task, tresult in ret.items():
            _dict = results if tresult['result'] else fails
            _dict[task] = {
                'comment': tresult.get('comment'),
                'changes': tresult.get('changes')
            }
        return results, fails


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHResultParser:

    @classmethod
    def _sanitize_key(cls, key):
        return (
            'jresult' if key == 'return' else
            key.lower().replace('-', '_').lstrip('_')
        )

    @classmethod
    def _verify(cls, res_t: Type[SaltSSHResultBase], data: Dict) -> bool:
        required = [
            k for k, v in attr.fields_dict(res_t).items()
            if (
                v.default is attr.NOTHING and
                k not in attr.fields_dict(SaltSSHResultBase)
            )
        ]
        return not (set(required) - set(data))

    @classmethod
    def from_salt_res(cls, data: Any, cmd_args_view: Dict):
        if type(data) is dict:
            _data = {cls._sanitize_key(k): v for k, v in data.items()}
            _types = [
                SaltSSHSimpleResult,
                (
                    SaltSSHStateJobResult
                    if cmd_args_view['fun'].startswith('state.')
                    else SaltSSHJobResult
                )
            ]
            for res_t in _types:
                if cls._verify(res_t, _data):
                    # TODO IMPROVE EOS-8473 makes sense
                    #      to place non-sanitized fields into other
                    other = {
                        k: _data.pop(k) for k in list(_data)
                        if (
                            k not in attr.fields_dict(res_t) or
                            k in attr.fields_dict(SaltSSHResultBase)
                        )
                    }
                    return res_t(data, other=other, **_data)

        return SaltSSHRawResult(data)


# TODO TYPE
# TODO TEST
@attr.s(auto_attribs=True)
class SaltClientResult:
    _prvsnr_type_ = True

    raw: Any
    cmd_args_view: Dict
    client: Dict = None
    results: Any = attr.ib(init=False, default=attr.Factory(dict))
    fails: Any = attr.ib(init=False, default=attr.Factory(dict))

    def __attrs_post_init__(self):
        # TODO is it a valid case actually ?
        if type(self.raw) is not dict:
            self.results = self.raw
        else:
            self._parse_raw_dict()

    def _parse_raw_dict(self):
        # TODO HARDEN check format of result
        for target, job_result in self.raw.items():
            ret = None
            if type(job_result) is dict:
                # result format as a part of job differs (async result) from
                # sync case:
                #   - 'ret' for sync
                #   - 'return' for async
                ret = job_result.get('ret', job_result.get('return'))
            elif job_result is False:
                # TODO IMPROVE explore salt docs/code for that,
                #      currently it's only an observation
                self.fails[target] = 'no connection to minion'

            if ret is None:
                self.results[target] = job_result
                continue
            else:
                self.results[target] = ret

            _fails = {}
            if job_result.get('retcode') != 0:
                if (
                    self.cmd_args_view['fun'].startswith('state.')
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


@attr.s(auto_attribs=True)
class SaltCallerClientResult(SaltClientResult):
    def __attrs_post_init__(self):
        self.raw = {
            'local': {
                'ret': self.raw,
                # XXX not declared salt internals, no other way to
                #     detect a failure
                'retcode': self.client.sminion.functions.pack[
                    '__context__'].get('retcode', 0)
            }
        }
        super().__attrs_post_init__()

    def _parse_raw_dict(self):
        ret = self.raw['local']['ret']

        if (
            self.cmd_args_view['fun'].startswith('state.')
            and (type(ret) is dict)
        ):
            self.results['local'] = ret

            _fails = self._get_state_fails(ret)
            if _fails:
                self.fails['local'] = _fails
        else:
            super()._parse_raw_dict()


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHClientResult(SaltClientResult):
    def _parse_raw_dict(self):
        for target, job_result in self.raw.items():
            ssh_res = SaltSSHResultParser.from_salt_res(
                job_result, self.cmd_args_view
            )
            self.results[target] = ssh_res.result
            if ssh_res.fail is not None:
                self.fails[target] = ssh_res.fail


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
    # FIXME EOS-14233 by some reason pillar.item result are not updated
    #       for old handlers even if refresh step is called
    if not _salt_caller_local or True:
        __opts__ = salt.config.minion_config('/etc/salt/minion')
        __opts__['file_client'] = 'local'
        _salt_caller_local = Caller(mopts=__opts__)
    return _salt_caller_local


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltClientBase(ABC):
    c_path: str = '/etc/salt/master'

    @property
    @abstractmethod
    def _cmd_args_t(self) -> Type[SaltClientArgsBase]:
        ...

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResult]:
        return SaltClientResult

    @abstractmethod
    def _run(self, cmd_args: SaltClientArgsBase):
        ...

    def parse_res(
        self, salt_res, cmd_args_view: Dict
    ) -> SaltClientResult:
        if not salt_res:
            raise SaltNoReturnError(
                cmd_args_view, 'Empty salt result: {}'.format(salt_res)
            )
        return self._salt_client_res_t(salt_res, cmd_args_view)

    def run(
        self,
        fun: str,
        targets: str = ALL_MINIONS,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        secure=False,
        **kwargs
    ):
        if targets == LOCAL_MINION:
            targets = local_minion_id()

        # XXX Caller for local minion commands works not smoothly,
        #     issues with ioloop, possibly related one
        #     https://github.com/saltstack/salt/issues/46905
        # return _salt_caller_cmd(fun, *args, **kwargs)

        # TODO log username / password ??? / eauth
        cmd_args = self._cmd_args_t(
            targets, fun, fun_args, fun_kwargs, kw=kwargs,
            secure=secure
        )

        logger.debug(
            f"Running function '{fun}' on '{targets}', args: {cmd_args}"
        )

        # TODO IMPROVE EOS-14361 make a View class instead
        cmd_args_view = cmd_args._as_dict()

        try:
            salt_res = self._run(cmd_args)
        except Exception as exc:
            logger.error(
                "salt command failed, reason {}, args {}"
                .format(exc, cmd_args_view))
            # TODO too generic
            raise SaltCmdRunError(cmd_args_view, exc) from exc

        res = self.parse_res(salt_res, cmd_args_view)

        if res.fails:
            raise SaltCmdResultError(cmd_args_view, res.fails)
        else:
            try:
                logger.debug(
                    f"Function '{fun}' on '{targets}' "
                    f"resulted in {pformat(res.results)}"
                )
            except Exception as exc:
                if (type(exc).__name__ == 'OSError' and exc.strerror == 'Message too long'):  # noqa: E501
                    logger.exception("Exception Skipped: {}".format(str(exc.strerror)))  # noqa: E501
                else:
                    raise exc

            return res.results

    def state_apply(self, state: str, targets=ALL_MINIONS, **kwargs):
        return self.run(
            'state.apply', fun_args=[state], targets=targets, **kwargs
        )

    def cmd_run(self, cmd: str, targets=ALL_MINIONS, **kwargs):
        return self.run(
            'cmd.run', fun_args=[cmd], targets=targets, **kwargs
        )

    def state_single(
        self,
        state_fun: str,
        fun_args: Union[List, Tuple, None] = None,
        **kwargs
    ):
        return self.run(
            'state.single',
            fun_args=[state_fun] + list(fun_args or []),
            **kwargs
        )


"""
# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltClient(SaltClientBase):
    # FIXME
    _client: SSHClient = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        self._client = LocalClient(c_path=str(self.c_path))

    @property
    def _cmd_args_t(self) -> Type[SaltClientArgsBase]:
        return SaltClientArgs

    def _run(self, cmd_args: SaltClientArgs):
        _cmd_f = (
            self._client.cmd_async if cmd_args.nowait else self._client.cmd
        )
        return _cmd_f(*cmd_args.args, **cmd_args.kwargs)

    # FIXME
    def run(self, *args, roster_file=None, **kwargs):
        if roster_file is None:
            roster_file = self.roster_file
        if roster_file:
            kwargs['roster_file'] = roster_file
        return super().run(*args, **kwargs)
"""


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHClient(SaltClientBase):
    roster_file: str = None
    ssh_options: Optional[Dict] = None

    _client: SSHClient = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        self._client = SSHClient(c_path=str(self.c_path))

    @property
    def _cmd_args_t(self) -> Type[SaltClientArgsBase]:
        return SaltSSHArgs

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResult]:
        return SaltSSHClientResult

    def _run(self, cmd_args: SaltSSHArgs):
        salt_logger = logging.getLogger('salt.client.ssh')
        salt_log_level = None

        if cmd_args.secure and salt_logger.isEnabledFor(logging.DEBUG):
            salt_log_level = salt_logger.getEffectiveLevel()
            salt_logger.setLevel(logging.INFO)

        try:
            return self._client.cmd(*cmd_args.args, **cmd_args.kwargs)
        finally:
            if salt_log_level is not None:
                salt_logger.setLevel(salt_log_level)

    # TODO TEST EOS-8473
    def ensure_access(
        self, targets: List, bootstrap_roster_file=None
    ):
        for target in targets:
            try:
                # try to reach using default (class-level) settings
                self.run(
                    'uname',
                    targets=target,
                    raw_shell=True
                )
            except SaltCmdResultError as exc:
                reason = exc.reason.get(target)
                roster_file = exc.cmd_args.get('kw').get('roster_file')

                if roster_file and ('Permission denied' in reason):
                    roster = load_yaml(roster_file)

                    if bootstrap_roster_file:
                        # NOTE assumptions:
                        #   - python3 is already there since it can be
                        #     installed using the bootstrap key
                        #     (so salt modules might be used now)
                        #   - bootstrap key is availble in salt-ssh file roots

                        self.run(
                            'state.single',
                            fun_args=['file.directory'],
                            fun_kwargs=dict(name='~/.ssh', mode=700),
                            targets=target,
                            roster_file=bootstrap_roster_file
                        )

                        # inject production access public key
                        # FIXME hardcoded 'root'
                        self.run(
                            'state.single',
                            fun_args=['ssh_auth.present'],
                            fun_kwargs=dict(
                                name=None,
                                user=roster.get(target, {}).get(
                                    'user', 'root'
                                ),
                                # FIXME hardcoded path to production pub key
                                source="salt://provisioner/files/minions/all/id_rsa_prvsnr.pub"  # noqa: E501
                            ),
                            targets=target,
                            roster_file=bootstrap_roster_file
                        )
                    else:
                        copy_id(
                            host=roster.get(target, {}).get('host'),
                            user=roster.get(target, {}).get('user'),
                            port=roster.get(target, {}).get('port'),
                            priv_key_path=roster.get(target, {}).get('priv'),
                            ssh_options=exc.cmd_args.get('kw').get(
                                'ssh_options'
                            ),
                            force=True
                        )
                else:
                    raise

    # TODO TEST EOS-8473
    def ensure_python3(
        self,
        targets: List,
        roster_file=None
    ):
        for target in targets:
            try:
                self.run(
                    'python3 --version',
                    targets=target,
                    roster_file=roster_file,
                    raw_shell=True
                )
            except SaltCmdResultError as exc:
                reason = exc.reason.get(target)
                # TODO IMPROVE EOS-8473 better search string / regex
                roster_file = exc.cmd_args.get('kw').get('roster_file')
                if roster_file and ("not found" in reason):
                    self.run(
                        'yum install -y python3',
                        targets=target,
                        roster_file=roster_file,
                        ssh_options=exc.cmd_args.get('kw').get('ssh_options'),
                        raw_shell=True
                    )
                else:
                    raise

    # TODO TEST EOS-8473
    def ensure_ready(
            self, targets: List, bootstrap_roster_file: Optional[Path] = None,
    ):
        if bootstrap_roster_file:
            self.ensure_python3(targets, roster_file=bootstrap_roster_file)

        self.ensure_access(
            targets,
            bootstrap_roster_file=bootstrap_roster_file
        )

        if not bootstrap_roster_file:
            self.ensure_python3(targets)

    # FIXME issues:
    #   1. not properly processed error, e.g.:
    #
    #        self.run(
    #            'state.single',
    #            fun_args=['ssh_auth.present'],
    #            fun_kwargs=dict(
    #                user=roster.get(target, {}).get(
    #                    'user', 'root'
    #                ),
    #                source=f"{priv_file}.pub"
    #            ),
    #            targets=target,
    #            roster_file=bootstrap_roster_file
    #        )
    #
    #        will return with success but salt actually error takes place:
    #
    #        TypeError encountered executing state.single: single() missing 1
    #        required positional argument: 'name'

    # TODO TYPE EOS-8473
    def run(self, *args, roster_file=None, ssh_options=None, **kwargs):
        if roster_file is None:
            roster_file = self.roster_file
        if roster_file:
            kwargs['roster_file'] = str(roster_file)
        if ssh_options is None:
            ssh_options = self.ssh_options
        if ssh_options:
            kwargs['ssh_options'] = ssh_options
        return super().run(*args, **kwargs)


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


def _salt_runner_cmd(  # noqa: C901 FIXME
    fun: str,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    nowait=False,
    secure=False,
    **kwargs
):
    # TODO FEATURE not yet supported
    if nowait:
        raise NotImplementedError(
            'async calls for RunnerClient are not supported yet'
        )

    # TODO log username / password ??? / eauth
    cmd_args = SaltRunnerArgs(
        fun, fun_args, fun_kwargs, nowait, kw=kwargs,
        secure=secure
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

    # TODO IMPROVE EOS-14361 make a View class instead
    cmd_args_view = cmd_args._as_dict()

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
        logger.error(
            "salt command failed, reason {}, args {}"
            .format(exc, cmd_args_view))
        raise SaltCmdRunError(cmd_args_view, exc) from exc

    if not salt_res:
        raise SaltNoReturnError(
            cmd_args_view, 'Empty salt result: {}'.format(salt_res)
        )

    if type(salt_res) is not dict:
        reason = (
                'RunnerClient result type is not a dictionary: {}'
                .format(type(salt_res))
            )
        logger.error(
            "salt command failed, reason {}, args {}"
            .format(reason, cmd_args_view))
        raise SaltCmdRunError(
            cmd_args_view, reason
        )

    if nowait:
        return salt_res

    if eauth:
        if 'data' not in salt_res:
            reason = (
                    'no data key in RunnerClient result dictionary: {}'
                    .format(salt_res)
                )
            logger.error(
                "salt command failed, reason {}, args {}"
                .format(reason, cmd_args_view))
            raise SaltCmdRunError(
                cmd_args_view, reason
            )
        res = salt_res['data']
    else:
        res = salt_res

    try:
        res = SaltRunnerResult.from_salt_res(res)
    except TypeError:
        msg = 'Failed to parse salt runner result: {}'.format(salt_res)
        logger.exception(msg)
        raise SaltCmdRunError(cmd_args_view, msg)

    if res.success:
        return res.result
    else:
        raise SaltCmdResultError(cmd_args_view, res.result)


# TODO TEST
# TODO DRY
def runner_function_run(
    fun,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    secure=False,
    **kwargs
):
    logger.debug(
        "Running runner function '{}', fun_args: {},"
        " fun_kwargs: {}, kwargs: {}"
        .format(
            fun,
            (SECRET_MASK if secure else fun_args),
            (SECRET_MASK if secure else fun_kwargs),
            kwargs
        )
    )

    try:
        res = _salt_runner_cmd(
            fun, fun_args=fun_args, fun_kwargs=fun_kwargs,
            secure=secure, **kwargs
        )
    except Exception:
        logger.exception("Salt runner command failed")
        raise

    logger.debug(
        f"Runner function '{fun}' "
        f"resulted in {pformat(res)}"
    )

    return res


# TODO LOGGING better logging coverage
def _salt_client_cmd(
    targets: str,
    fun: str,
    fun_args: Union[Tuple, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    nowait=False,
    secure=False,
    local=False,
    **kwargs
):
    if local:
        # TODO IMPROVE some of the arguments would be silently ignored here
        cmd_args = SaltCallerArgs(
            fun=fun, fun_args=fun_args, fun_kwargs=fun_kwargs, secure=secure
        )
    else:
        # TODO log username / password ??? / eauth
        cmd_args = SaltClientArgs(
            targets, fun, fun_args, fun_kwargs, kw=kwargs, nowait=nowait,
            secure=secure
        )
        _set_auth(cmd_args.kw)
        cmd_args.kw['full_return'] = True

    # TODO IMPROVE EOS-14361 make a View class instead
    cmd_args_view = cmd_args._as_dict()

    if local:
        client = salt_caller_local()
        salt_res_t = SaltCallerClientResult
    else:
        client = salt_local_client()
        salt_res_t = SaltClientResult

    try:
        if local:
            _cmd_f = client.cmd
        else:
            _cmd_f = (client.cmd_async if nowait else client.cmd)

        salt_res = _cmd_f(*cmd_args.args, **cmd_args.kwargs)
    except Exception as exc:
        logger.error(
                "salt command failed, reason {}, args {}"
                .format(repr(exc), cmd_args_view))
        # TODO too generic
        raise SaltCmdRunError(cmd_args_view, repr(exc)) from exc

    if not salt_res:
        reason = (
            'Async API returned empty result: {}'.format(salt_res) if nowait
            else 'Empty salt result: {}'.format(salt_res)
        )
        raise SaltNoReturnError(cmd_args_view, reason)

    if nowait:
        return salt_res

    res = salt_res_t(salt_res, cmd_args_view, client)

    if res.fails:
        raise SaltCmdResultError(cmd_args_view, res.fails)
    else:
        return res.results


# TODO test
def function_run(
    fun,
    targets=ALL_MINIONS,
    fun_args: Union[Tuple, List, None] = None,
    fun_kwargs: Union[Dict, None] = None,
    secure=False,
    **kwargs
):
    if targets == LOCAL_MINION:
        targets = local_minion_id()

    # XXX Caller for local minion commands works not smoothly,
    #     issues with ioloop, possibly related one
    #     https://github.com/saltstack/salt/issues/46905
    # return _salt_caller_cmd(fun, *args, **kwargs)

    logger.debug(
        "Running function '{}' on '{}', fun_args: {},"
        " fun_kwargs: {}, kwargs: {}"
        .format(
            fun,
            targets,
            (SECRET_MASK if secure else fun_args),
            (SECRET_MASK if secure else fun_kwargs),
            kwargs
        )
    )

    try:
        res = _salt_client_cmd(
            targets, fun, fun_args=fun_args, fun_kwargs=fun_kwargs,
            secure=secure, **kwargs
        )
    except Exception:
        logger.exception("Salt client command failed")
        raise

    logger.debug(
        f"Function '{fun}' on '{targets}' "
        f"resulted in {pformat(res)}"
    )

    return res


def pillar_get(targets=ALL_MINIONS, **kwargs):
    return function_run('pillar.items', targets=targets, **kwargs)


def pillar_refresh(targets=ALL_MINIONS):
    return function_run('saltutil.refresh_pillar', targets=targets)


# TODO test
# TODO IMPROVE EOS-9484 think about better alternative to get separated
#      stderr and stdout streams that makes sense sometimes even if a command
#      don't fail (e.g. use 'run_all' instead)
def cmd_run(
    cmd,
    targets=ALL_MINIONS,
    background=False,
    timeout=None,
    fun_kwargs: Optional[Dict] = None,
    **kwargs
):
    if fun_kwargs is None:
        fun_kwargs = {}
    # TODO IMPROVE EOS-12076 wrapper args vs direct salt's ones
    fun_kwargs['bg'] = background
    return function_run(
        'cmd.run',
        fun_args=[cmd],
        fun_kwargs=fun_kwargs,
        targets=targets,
        timeout=timeout,
        **kwargs
    )


# TODO TEST EOS-12076
def sls_exists(state, targets=ALL_MINIONS, summary_only=True, **kwargs):
    res = function_run(
        'state.sls_exists',
        fun_args=[state],
        targets=targets,
        **kwargs
    )

    if summary_only:
        return set(res.values()) == {True}
    else:
        return res

# TODO FIXME test
def ping(targets=ALL_MINIONS, **kwargs):
    return function_run('test.ping', targets=targets, **kwargs)


# TODO FIXME test
def list_minions(targets=ALL_MINIONS):
    return list(ping(targets))


# TODO TEST
def process_provisioner_cmd_res(res):
    if not isinstance(res, dict) or len(res) != 1:
        raise ProvisionerError(
            f'Expected a dictionary of len = 1, provided: {type(res)}, {res}'
        )

    # FIXME EOS-9581 it might be other minion id in case of HA
    if local_minion_id() not in res:
        logger.warning(
            f"local minion id {local_minion_id()} is not listed "
            f"in results: {list(res)}, might be initiated by other node"
        )

    # provisioner cli output
    prvsnr_res = next(iter(res.values()))
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
                'SaltCmdResultError is unexpected here: {!r}'.format(exc)
            ) from exc
        else:
            return process_provisioner_cmd_res(exc.reason)
    else:
        if nowait:
            return res
        else:
            return process_provisioner_cmd_res(res)


def states_apply(
    states: List[Union[str, State]], targets=ALL_MINIONS, **kwargs
):
    # TODO multiple states at once
    ret = {}
    for state in states:
        state = State(state)
        res = function_run(
            'state.apply', fun_args=[state.name], targets=targets, **kwargs
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
def copy_to_file_roots(
    source: Union[str, Path],
    dest: Union[str, Path],
    file_root: Optional[Path] = None
):
    if file_root is None:
        file_root = PRVSNR_USER_FILEROOT_DIR

    source = Path(str(source))
    dest = file_root / dest

    if not source.exists():
        raise ValueError('{} not found'.format(source))

    if source.is_dir():
        # TODO
        #  - file.recurse expects only dirs from salt-master file roots
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

    # TODO DOC
    # ensure it would be visible for salt-master / salt-minions
    runner_function_run(
        'fileserver.clear_file_list_cache',
        fun_kwargs=dict(backend='roots')
    )
    return dest


# TODO tests
@attr.s(auto_attribs=True)
class StatesApplier:
    @staticmethod
    def apply(
        states: List[State], targets: str = ALL_MINIONS, **kwargs
    ) -> None:
        if states:
            return states_apply(states=states, targets=targets, **kwargs)


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
                # FIXME EOS-14361 that might disclosure some secure data
                #       since 'secure' arg is not set
                cmd_args = SaltClientArgs(
                    targets=job.minions,  # TODO ??? or job.target
                    fun=job.function,
                    fun_args=job.arguments
                )
                cmd_args_view = cmd_args._as_dict()
                client_res = SaltClientResult(job.result, cmd_args_view)
                return process_provisioner_cmd_res(client_res.results)
        else:
            raise PrvsnrCmdNotFoundError(jid)


def get_last_txn_ids(targets: str, multiple_targets_ok: bool = False) -> dict:
    """
    Get latest transition id number from yum transition history

    Parameters
    ----------
    targets: str
        Salt targets

    multiple_targets_ok: bool
        Flag to indicate that we are waiting only for one transition id number.
        If it is `True`, multiple targets are allowed in the result dictionary,
        otherwise, an `ValueError` exception will be raised.

    Returns
    -------
    dict
        map of targets and their corresponding yum history transaction numbers

    """
    # TODO IMPROVE EOS-9484  stderrr might include valuable info
    txn_ids = cmd_run(("yum history 2>/dev/null | grep ID -A 2 | "
                       "tail -n1 | awk '{print $1}'"),
                      targets=targets)

    if not multiple_targets_ok and (len(txn_ids) > 1):
        err_msg = ("Multiple targetting is not expected, "
                   f"matched targets: {list(txn_ids)} for '{targets}'")
        logger.error(err_msg)
        raise ValueError(err_msg)

    logger.debug(f'Rollback txns ids: {txn_ids}')
    return txn_ids


# TODO test
@attr.s(auto_attribs=True)
class YumRollbackManager:
    targets: str = ALL_MINIONS
    multiple_targets_ok: bool = False
    pre_rollback_cb: Optional[Callable] = None
    _last_txn_ids: Dict = attr.ib(init=False, default=attr.Factory(dict))
    _rollback_error: Union[Exception, None] = attr.ib(init=False, default=None)

    @staticmethod
    def _yum_rollback(txn_id, target):
        # TODO IMPROVE minion might be stopped at that moment,
        #      option - use some ssh fallback
        logger.info(f"Starting rollback on target {target}")

        cmd = (f'yum history rollback -y {txn_id}')
        logger.debug(f'Executing "{cmd}" on {target}')
        cmd_run(
            cmd,
            targets=target
        )

        logger.info(
            f"Rollback on target {target} is completed"
        )

    def __enter__(self):
        self._last_txn_ids = get_last_txn_ids(
                                targets=self.targets,
                                multiple_targets_ok=self.multiple_targets_ok)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return

        # TODO TEST EOS-8940
        if self.pre_rollback_cb:
            try:
                self.pre_rollback_cb(self, exc_type, exc_value, exc_traceback)
            except Exception as exc:
                self._rollback_error = exc
                return

        try:
            for target, txn_id in self._last_txn_ids.items():
                self._yum_rollback(txn_id, target)
        except Exception as exc:
            logger.debug(f'Exception occured: {exc}')
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


# salt-ssh possible formats (TODO ??? salt docs for that)


"""
{
    'srvnode2': {
        'fun': 'test.ping',
        'fun_args': [],
        'id': 'srvnode2',
        'jid': '20200603135348953717',
        'retcode': 0,
        'return': True
    }
}
"""

"""
{
    'srvnode2': {
        'retcode': 0,
        'stderr': "Warning: Permanently added '[127.0.0.1]:2222' (ECDSA) "
                'to the list of known hosts.\r\n',
        'stdout': 'Loaded plugins: fastestmirror\n'
                'Loading mirror speeds from cached hostfile\n'
                ' * base: mirror.axelname.ru\n'
                ' * epel: mirror.datacenter.by\n'
                ' * extras: dedic.sh\n'
                ' * updates: mirrors.powernet.com.ru\n'
                'Package python3-3.6.8-13.el7.x86_64 already installed '
                'and latest version\n'
                'Nothing to do\n'
    }
}
"""


"""

{
    'srvnode2': {
        'fun': 'state.pkg',
        'fun_args': [...],
        'id': 'srvnode2',
        'jid': '20200603135634495984',
        'out': 'highstate',
        'retcode': 0,
        'return': {
            '<state-name-as-a-key>': {
                '__run_num__': 1,
                '__sls__': 'cortx_repos.install',
                '__state_ran__': False,
                'changes': {},
                'comment': '<some-comment>',
                'duration': 0.002,
                'result': True,
                'start_time': '13:56:34.598244'
            },
            ...
        }
    }
}
"""

"""
{
    'srvnode2': {
        '_error': 'Failed to return clean data',
        'retcode': 255,
        'stderr': "some stderr"
        'stdout': 'some stdout'
    }
}
"""

"""
{
    'srvnode2': {
        'fun': 'cmd.script',
        'fun_args': ['salt://firewall/files/firewall.sh'],
        'id': 'srvnode2',
        'jid': '20200603135016017125',
        'retcode': 0,
        'return': {
            'cache_error': True,
            'pid': 0,
             'retcode': 1,
             'stderr': '',
             'stdout': ''
        }
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
        #    unnecessary connections with salt-master
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
