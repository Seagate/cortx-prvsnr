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
from typing import (
    List, Union, Dict, Tuple, Any, Type
)
import logging
from pprint import pformat

from ..vendor import attr
from ..config import (
   SECRET_MASK
)
from ..errors import (
    SaltNoReturnError,
    SaltCmdRunError, SaltCmdResultError
)

logger = logging.getLogger(__name__)


# TODO TEST
@attr.s(auto_attribs=True)
class SaltArgsBase:
    _prvsnr_type_ = True

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
        return (self.fun,)

    @property
    def kwargs(self):
        # FIXME check why 'arg' key is used here
        #       (looks like some client specific)
        return dict(arg=self.fun_args, kwarg=self.fun_kwargs, **self.kw)

    def __str__(self):
        """Return str presentation."""
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


@attr.s(auto_attribs=True)
class SaltClientResultBase:
    _prvsnr_type_ = True

    raw: Any
    cmd_args_view: Dict
    results: Any = attr.ib(init=False, default=attr.Factory(dict))
    fails: Any = attr.ib(init=False, default=attr.Factory(dict))


@attr.s(auto_attribs=True)
class SaltClientJIDResult(SaltClientResultBase):

    def __attrs_post_init__(self):
        """Do post init."""
        if not isinstance(self.raw, str):
            self.fails = (
                f'not a valid salt job ID value type: {type(self.raw)}'
            )

        try:
            self.results = int(self.raw)
        except ValueError:
            self.fails = (
                f'not a valid salt job ID value: {self.raw}'
            )


@attr.s(auto_attribs=True)
class SaltClientJobResult(SaltClientResultBase):

    def __attrs_post_init__(self):
        """Do post init."""
        # TODO is it a valid case actually ?
        if not isinstance(self.raw, dict):
            self.results = self.raw
        else:
            try:
                self._parse_raw_dict()
            except Exception as exc:
                self.results = self.raw
                self.fails = str(exc)

    def _parse_raw_dict(self):
        # TODO HARDEN check format of result
        for target, job_result in self.raw.items():
            ret = None
            if isinstance(job_result, dict):
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
                    and isinstance(ret, dict)
                ):
                    _fails = self._get_state_fails(ret)
                else:
                    _fails = ret

            if _fails:
                self.fails[target] = _fails

        # TODO TESTS
    @staticmethod
    def _get_state_fails(ret: Dict):
        fails = {}
        for task, tresult in ret.items():
            if not tresult['result']:
                fails[task] = {
                    'comment': tresult.get('comment'),
                    'changes': tresult.get('changes')
                }
        return fails


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltClientBase(ABC):
    c_path: str = None

    @property
    @abstractmethod
    def _cmd_args_t(self) -> Type[SaltArgsBase]:
        """Return type of arguments."""

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResultBase]:
        """Return client result type."""

    def _build_cmd_args(
        self,
        fun: str,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        secure=False,
        **kwargs
    ) -> SaltArgsBase:

        _kwargs = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(self._cmd_args_t)
        }

        return self._cmd_args_t(
            fun, fun_args=fun_args, fun_kwargs=fun_kwargs,
            kw=kwargs, secure=secure, **_kwargs
        )

    @abstractmethod
    def _run(self, cmd_args: SaltArgsBase):
        """Do salt call with provided arguments."""

    def _parse_res(
        self, salt_res, cmd_args_view: Dict
    ) -> SaltClientResultBase:
        return self._salt_client_res_t(salt_res, cmd_args_view)

    # TODO LOGGING ??? better logging coverage
    def run(
        self,
        fun: str,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        secure=False,
        **kwargs
    ):
        # XXX Caller for local minion commands works not smoothly,
        #     issues with ioloop, possibly related one
        #     https://github.com/saltstack/salt/issues/46905
        # return _salt_caller_cmd(fun, *args, **kwargs)

        # TODO log username / password ??? / eauth
        cmd_args = self._build_cmd_args(
            fun, fun_args, fun_kwargs, secure, **kwargs
        )

        # TODO IMPROVE EOS-14361 make a View class instead
        cmd_args_view = cmd_args._as_dict()

        logger.debug(
            f"'{type(self)}' client: Running function '{fun}' "
            f"with args: {cmd_args}"
        )

        try:
            salt_res = self._run(cmd_args)
        except Exception as exc:
            # TODO too generic
            raise SaltCmdRunError(cmd_args_view, repr(exc)) from exc

        if not salt_res:
            raise SaltNoReturnError(
                cmd_args_view, 'Empty salt result: {}'.format(salt_res)
            )

        res = self._parse_res(salt_res, cmd_args_view)

        if res.fails:
            raise SaltCmdResultError(cmd_args_view, res.fails)

        try:
            logger.debug(
                "'{}' client: Function '{}' resulted in: {}"
                .format(type(self), fun, pformat(res.results))
            )
        except Exception as exc:
            if (type(exc).__name__ == 'OSError' and exc.strerror == 'Message too long'):  # noqa: E501
                logger.exception("Exception Skipped: {}".format(str(exc.strerror)))  # noqa: E501
            else:
                raise exc

        return res.results

    def _fun_fun(
        self,
        fun,
        fun_fun: str,
        fun_args: Union[List, Tuple, None] = None,
        **kwargs
    ):
        return self.run(
            fun,
            fun_args=[fun_fun] + list(fun_args or []),
            **kwargs
        )

    def state_apply(self, state: str, **kwargs):
        return self.fun_fun('state.apply', state, **kwargs)

    def cmd_run(self, cmd: str, **kwargs):
        return self.fun_fun('cmd.run', cmd, **kwargs)

    def state_single(self, state_fun: str, **kwargs):
        return self.fun_fun('state.single', state_fun, **kwargs)

    def pillar_get(self, **kwargs):
        return self.run('pillar.items', **kwargs)
