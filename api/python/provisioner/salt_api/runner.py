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

import salt.config
from salt.runner import RunnerClient
from typing import (
    List, Dict, Any, Type, Union, Tuple, Optional
)
import logging

from .. import inputs
from ..vendor import attr

from .base import (
    SaltArgsBase,
    SaltClientBase,
    SaltClientResultBase,
    SaltClientJIDResult
)
from .auth import _set_auth

logger = logging.getLogger(__name__)


_salt_runner_client = None


def salt_runner_client():
    global _salt_runner_client
    if not _salt_runner_client:
        __opts__ = salt.config.client_config('/etc/salt/master')
        _salt_runner_client = RunnerClient(opts=__opts__)
    return _salt_runner_client


# TODO TEST
@attr.s(auto_attribs=True)
class SaltRunnerClientArgs(SaltArgsBase):
    pass


# TODO TEST
# TODO IMPROVE EOS-14361 optionally mask fun_args
@attr.s(auto_attribs=True)
class SaltRunnerSchemaResult:
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


# TODO TYPE
# TODO TEST
@attr.s(auto_attribs=True)
class SaltRunnerClientResult(SaltClientResultBase):

    def __attrs_post_init__(self):
        """Do post init."""
        if not isinstance(self.raw, dict):
            self.fails = (
                "RunnerClient result type is not a dictionary: "
                f"{type(self.raw)}"
            )
        else:
            res = self.raw

            if 'username' in self.cmd_args_view['kw']:
                try:
                    res = self.raw['data']
                except KeyError:
                    # TODO IMPROVE EOS-14361 raw result might disclosure
                    #      the secrets from cmd args
                    self.fails = (
                        "no data key in RunnerClient result dictionary: "
                        f"{self.raw}"
                    )
                    return

            try:
                res = SaltRunnerSchemaResult.from_salt_res(res)
            except TypeError:
                # TODO IMPROVE EOS-14361 raw result might disclosure
                #      the secrets from cmd args
                res.fails = (
                    "Failed to parse salt runner result: "
                    f"{self.raw}"
                )
            else:
                self.results = res.result
                if not res.success:
                    self.fails = self.results


@attr.s(auto_attribs=True)
class SaltRunnerClient(SaltClientBase):
    c_path: str = attr.ib(
        default='/etc/salt/master',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config path"
            }
        }
    )
    shared: bool = False

    _client: RunnerClient = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        """Do post init."""
        if self.shared:
            self._client = salt_runner_client()
        else:
            __opts__ = salt.config.client_config(str(self.c_path))
            self._client = RunnerClient(opts=__opts__)

    @property
    def _cmd_args_t(self) -> Type[SaltArgsBase]:
        return SaltRunnerClientArgs

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResultBase]:
        return SaltRunnerClientResult

    def _build_cmd_args(
        self,
        fun: str,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        secure=False,
        **kwargs
    ) -> SaltArgsBase:

        cmd_args = super()._build_cmd_args(
            fun, fun_args, fun_kwargs, secure, **kwargs
        )

        _set_auth(cmd_args.kw)

        if 'username' not in cmd_args.kw:
            cmd_args.kw['print_event'] = False
            cmd_args.kw['full_return'] = True

        return cmd_args

    def _run(self, cmd_args: SaltArgsBase):
        if 'username' in cmd_args.kw:
            low = dict(fun=cmd_args.fun, **cmd_args.kwargs)
            return self._client.cmd_sync(low, full_return=True)
        else:
            return self._client.cmd(*cmd_args.args, **cmd_args.kwargs)

    def _fun_fun(
        self,
        fun,
        fun_fun: str,
        fun_args: Optional[Union[List, Tuple]] = None,
        **kwargs
    ):
        fun_args = [fun_fun] + list(fun_args or [])
        return super()._fun_fun(
            'salt.cmd', fun, fun_args=fun_args, **kwargs
        )


@attr.s(auto_attribs=True)
class SaltRunnerAsyncClient(SaltRunnerClient):

    def __attrs_post_init__(self):
        """Do post init."""
        raise NotImplementedError(
            'async calls for RunnerClient are not supported yet'
        )

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResultBase]:
        return SaltClientJIDResult

    def _build_cmd_args(
        self,
        fun: str,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        secure=False,
        **kwargs
    ) -> SaltArgsBase:

        cmd_args = super()._build_cmd_args(
            fun, fun_args, fun_kwargs, secure, **kwargs
        )

        if 'username' not in cmd_args.kw:
            raise NotImplementedError(
                'async calls without external auth for RunnerClient'
                ' are not supported yet'
            )

        return cmd_args

    def _run(self, cmd_args: SaltArgsBase):
        low = dict(fun=cmd_args.fun, **cmd_args.kwargs)
        return salt_runner_client().cmd_async(low, full_return=True)
