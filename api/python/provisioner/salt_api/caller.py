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
from salt.client import Caller
from typing import (
    Dict, Type
)
import logging

from .. import inputs
from ..vendor import attr

from .base import (
    SaltArgsBase,
    SaltClientResultBase
)
from .base import (
    SaltClientJobResult,
    SaltClientBase
)


logger = logging.getLogger(__name__)


_salt_caller = None
_salt_caller_local = None
_local_minion_id = None


# XXX Caller for local minion commands works not smoothly,
#     issues with ioloop, possibly related one
#     https://github.com/saltstack/salt/issues/46905
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


@attr.s(auto_attribs=True)
class SaltCallerArgs(SaltArgsBase):
    @property
    def args(self):
        return (self.fun, *self.fun_args)

    @property
    def kwargs(self):
        return self.fun_kwargs


@attr.s(auto_attribs=True)
class SaltCallerClientResult(SaltClientJobResult):
    client: Caller

    def __attrs_post_init__(self):
        """Do post init."""
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
            and isinstance(ret, dict)
        ):
            self.results['local'] = ret

            _fails = self._get_state_fails(ret)
            if _fails:
                self.fails['local'] = _fails
        else:
            super()._parse_raw_dict()


@attr.s(auto_attribs=True)
class SaltCallerClientBase(SaltClientBase):
    c_path: str = attr.ib(
        default='/etc/salt/minion',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config path"
            }
        }
    )

    shared: bool = False
    _local: bool = True

    _client: Caller = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        """Do post init."""
        if self.shared:
            if self._local:
                self._client = salt_caller_local()
            else:
                self._client = salt_caller()
        else:
            __opts__ = salt.config.minion_config(str(self.c_path))
            if self._local:
                __opts__['file_client'] = 'local'
            self._client = Caller(mopts=__opts__)

    @property
    def _cmd_args_t(self) -> Type[SaltArgsBase]:
        return SaltCallerArgs

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResultBase]:
        return SaltCallerClientResult

    def _run(self, cmd_args: SaltArgsBase):
        # FIXME
        return self._client.cmd(*cmd_args.args, **cmd_args.kwargs)

    def _parse_res(
        self, salt_res, cmd_args_view: Dict
    ) -> SaltClientResultBase:
        return self._salt_client_res_t(
            salt_res, cmd_args_view, self._client
        )


@attr.s(auto_attribs=True)
class SaltLocalCallerClient(SaltCallerClientBase):
    _local: bool = attr.ib(init=False, default=True)


@attr.s(auto_attribs=True)
class SaltCallerClient(SaltCallerClientBase):
    _local: bool = attr.ib(init=False, default=False)


def local_minion_id():
    global _local_minion_id
    if not _local_minion_id:
        _local_minion_id = SaltLocalCallerClient().run(
            'grains.get', fun_args=['id']
        )['local']
    return _local_minion_id
