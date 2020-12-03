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

from salt.client import LocalClient
from typing import (
    Dict, Type, Union, Tuple
)
import logging

from .. import inputs
from ..vendor import attr
from ..config import (
   ALL_MINIONS, LOCAL_MINION
)
# from ..commands._basic import RunArgs

from .caller import local_minion_id
from .base import (
    SaltArgsBase,
    SaltClientBase,
    SaltClientResultBase,
    SaltClientJobResult,
    SaltClientJIDResult
)
from .auth import _set_auth

logger = logging.getLogger(__name__)

_salt_local_client = None


def salt_local_client():
    global _salt_local_client
    # TODO IMPROVE in case of minion retsart old handler will
    #      lead to Authentication error, so always recreate it
    #      as a workaround for now
    if not _salt_local_client or True:
        _salt_local_client = LocalClient()
    return _salt_local_client


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltLocalClientArgs(SaltArgsBase):
    targets: str = attr.ib(
        converter=(
            lambda v: local_minion_id() if v == LOCAL_MINION else str(v)
        ),
        default=ALL_MINIONS
    )

    @property
    def args(self):
        return (self.targets, self.fun)


@attr.s(auto_attribs=True)
class SaltLocalClientResult(SaltClientJobResult):
    pass


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltLocalClient(SaltClientBase):
    c_path: str = attr.ib(
        default='/etc/salt/master',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config path"
            }
        }
    )
    # targets: str = RunArgs.targets
    targets: str = attr.ib(
        default=ALL_MINIONS,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "command's host targets"
            }
        }
    )

    shared: bool = False

    _client: LocalClient = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        """Do post init."""
        if self.shared:
            self._client = salt_local_client()
        else:
            self._client = LocalClient(c_path=str(self.c_path))

    @property
    def _cmd_args_t(self) -> Type[SaltArgsBase]:
        return SaltLocalClientArgs

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResultBase]:
        return SaltLocalClientResult

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
        cmd_args.kw['full_return'] = True

        return cmd_args

    def _run(self, cmd_args: SaltArgsBase):
        return self._client.cmd(*cmd_args.args, **cmd_args.kwargs)

    def run(
        self,
        fun: str,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        secure=False,
        **kwargs
    ):
        targets = kwargs.pop('targets', self.targets)
        if targets:
            kwargs['targets'] = targets

        return super().run(fun, fun_args, fun_kwargs, secure, **kwargs)


@attr.s(auto_attribs=True)
class SaltLocalAsyncClient(SaltLocalClient):
    @property
    def _salt_client_res_t(self) -> Type[SaltClientResultBase]:
        return SaltClientJIDResult

    def _run(self, cmd_args: SaltArgsBase):
        return self._client.cmd_async(*cmd_args.args, **cmd_args.kwargs)
