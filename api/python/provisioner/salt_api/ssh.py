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

from abc import ABC
from typing import (
    List, Dict, Any, Type, Optional, Union, Tuple
)
from salt.client.ssh.client import SSHClient
from pathlib import Path
import logging

from .. import inputs, config
from ..vendor import attr
from ..ssh import copy_id
from .. import utils
from ..errors import (
    SaltCmdResultError
)
# from ..paths import (
#     USER_SHARED_PILLAR,
#    GLUSTERFS_VOLUME_PILLAR_DIR
# )
from ..cli_parser import KeyValueListAction
# from ..commands._basic import RunArgs
from ..node import Node

from .base import (
    SaltArgsBase,
    SaltClientBase,
    SaltClientResultBase,
    SaltClientJobResult,
    converter__fileroot_path,
    converter__pillar_path
)
from .client import (
    SaltLocalClientArgs
)


logger = logging.getLogger(__name__)


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHArgs(SaltLocalClientArgs):
    pass


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHResultSchemaBase(ABC):
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
class SaltSSHRawResultSchema(SaltSSHResultSchemaBase):
    other: Dict = attr.ib(init=False, default=attr.Factory(dict))

    def __attrs_post_init__(self):
        """Do post init."""
        self._result = self.raw


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHSimpleResultSchema(SaltSSHResultSchemaBase):
    retcode: int
    stderr: str
    stdout: str

    def __attrs_post_init__(self):
        """Do post init."""
        self._result = self.stdout
        if self.retcode:
            self._fail = f'STDERR: {self.stderr}, STDOUT: {self.stdout}'


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHJobDummyResultSchema(SaltSSHResultSchemaBase):
    jresult: Any

    def __attrs_post_init__(self):
        """Do post init."""
        # XXX it never fails just returns
        self._result = self.jresult


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHJobResultSchema(SaltSSHJobDummyResultSchema):
    retcode: int
    jid: str
    fun: str
    fun_args: List

    def __attrs_post_init__(self):
        """Do post init."""
        super().__attrs_post_init__()

        # TODO IMPROVE better error presentation
        if self.retcode or (
            isinstance(self._result, dict) and
            self._result.get('retcode')
        ):
            self._fail = self._result


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHStateJobResultSchema(SaltSSHJobResultSchema):

    def __attrs_post_init__(self):
        """Do post init."""
        self._result, _fail = self._get_state_results(self.jresult)
        if _fail:
            self._fail = _fail

    # TODO IMPROVE EOS-8473
    @staticmethod
    def _get_state_results(ret: Dict):
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
    def _verify(cls, res_t: Type[SaltSSHResultSchemaBase], data: Dict) -> bool:
        required = [
            k for k, v in attr.fields_dict(res_t).items()
            if (
                v.default is attr.NOTHING and
                k not in attr.fields_dict(SaltSSHResultSchemaBase)
            )
        ]
        return not (set(required) - set(data))

    @classmethod
    def from_salt_res(cls, data: Any, cmd_args_view: Dict):
        if isinstance(data, dict):
            _data = {cls._sanitize_key(k): v for k, v in data.items()}
            _types = [
                SaltSSHSimpleResultSchema,
                (
                    SaltSSHStateJobResultSchema
                    if cmd_args_view['fun'].startswith('state.')
                    else SaltSSHJobResultSchema
                ),
                SaltSSHJobDummyResultSchema
            ]
            for res_t in _types:
                if cls._verify(res_t, _data):
                    # TODO IMPROVE EOS-8473 makes sense
                    #      to place non-sanitized fields into other
                    other = {
                        k: _data.pop(k) for k in list(_data)
                        if (
                            k not in attr.fields_dict(res_t) or
                            k in attr.fields_dict(SaltSSHResultSchemaBase)
                        )
                    }
                    return res_t(data, other=other, **_data)

        return SaltSSHRawResultSchema(data)


# TODO TEST EOS-8473
# FIXME not covered cases:
#   - no error raised:
#       - 'fun': 'state.apply', 'fun_args': ['r']:
#           {'srvnode-1': {'return': ["No matching sls found for 'r' in env 'base'"]}}  # noqa: E501
#       - 'fun': 'state.apply', 'fun_args': ['3']
#           {'srvnode-1': {'return': "TypeError encountered executing state.apply: 'int' object is not iterable"}}  # noqa: E501
#           Note. here salt-ssh just logs
#               salt.client.ssh - ERROR - [__init__.py:1251]: cmd:resource TypeError encountered executing state.apply: 'int' object is not iterable  # noqa: E501
@attr.s(auto_attribs=True)
class SaltSSHClientResult(SaltClientJobResult):
    def _parse_raw_dict(self):
        for target, job_result in self.raw.items():
            ssh_res = SaltSSHResultParser.from_salt_res(
                job_result, self.cmd_args_view
            )
            self.results[target] = ssh_res.result
            if ssh_res.fail is not None:
                self.fails[target] = ssh_res.fail


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class SaltSSHClient(SaltClientBase):
    c_path: str = attr.ib(
        default='/etc/salt/master',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config path"
            }
        },
        converter=utils.converter_path_resolved,
    )
    roster_file: str = attr.ib(
        default=config.SALT_ROSTER_DEFAULT,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "path to roster file"
            }
        },
        converter=utils.converter_path_resolved,
    )
    profile: str = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "path to ssh profile, if specified"
                    "'--c-path', '--roster-file', '--pillar-path'"
                    "and '--fileroot-path' options would be set "
                    "automatically"
                )
            }
        },
        converter=utils.converter_path_resolved
    )
    ssh_options: Optional[Dict] = attr.ib(
        default=attr.Factory(
            lambda: [
                'UserKnownHostsFile=/dev/null',
                'StrictHostKeyChecking=no'
            ]
        ),
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "ssh connection options",
                'metavar': 'KEY=VALUE',
                'nargs': '+',
                'action': KeyValueListAction
            }
        }
    )
    # targets: str = RunArgs.targets
    targets: str = attr.ib(
        default=config.ALL_MINIONS,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "command's host targets"
            }
        }
    )
    re_config: bool = False

    _client: SSHClient = attr.ib(init=False, default=None)
    _def_roster_data: Dict = attr.ib(init=False, default=attr.Factory(dict))

    def __attrs_post_init__(self):
        """Do post init."""

        if self.profile:
            paths = config.profile_paths(
                config.profile_base_dir(profile=self.profile)
            )
            self.c_path = paths['salt_master_file']
            self.roster_file = paths['salt_roster_file']
            self.fileroot_path = converter__fileroot_path(
                paths['salt_fileroot_dir']
            )
            self.pillar_path = converter__pillar_path(
                paths['salt_pillar_dir']
            )

        self._client_init()

        # if self.roster_file is None:
        #     path = USER_SHARED_PILLAR.all_hosts_path(
        #         'roster.sls'
        #     )
        #     if not path.exists():
        #        path = GLUSTERFS_VOLUME_PILLAR_DIR.all_hosts_path(
        #            'roster.sls'
        #        )

        #    if path.exists():
        #        self.roster_file = path

        if self.roster_file:
            logger.debug(f'default roster is set to {self.roster_file}')
            self._def_roster_data = utils.load_yaml(self.roster_file)

    def _client_init(self):
        self._client = SSHClient(c_path=str(self.c_path))

    @property
    def _cmd_args_t(self) -> Type[SaltArgsBase]:
        return SaltSSHArgs

    @property
    def _salt_client_res_t(self) -> Type[SaltClientResultBase]:
        return SaltSSHClientResult

    def _add_file_roots(self, roots: List[Path]):
        config = utils.load_yaml(self.c_path)
        for root in roots:
            if str(root) not in config['file_roots']['base']:
                config['file_roots']['base'].append(str(root))

        utils.dump_yaml(self.c_path, config)

        self._client_init()

    def add_file_roots(self, roots: List[Path]):
        if not self.re_config:
            raise RuntimeError('re-configuration is not allowed')

        return self._add_file_roots(roots)

    def roster_data(self, roster_file=None):
        if roster_file:
            return utils.load_yaml(roster_file)
        else:
            return self._def_roster_data

    def roster_targets(self, roster_file=None):
        return list(self.roster_data(roster_file))

    def roster_nodes(self, roster_file=None):
        return [
            Node(target, params['host'], params['user'], params['post'])
            for target, params in self.roster_data(roster_file).items()
        ]

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

    def run(
        self,
        fun: str,
        fun_args: Union[Tuple, None] = None,
        fun_kwargs: Union[Dict, None] = None,
        secure=False,
        **kwargs
    ):
        for arg in ('roster_file', 'ssh_options', 'targets'):
            arg_v = kwargs.pop(arg, None)
            if arg_v is None:
                arg_v = getattr(self, arg)
            if arg_v:
                kwargs[arg] = (
                    str(arg_v) if arg == 'roster_file' else arg_v
                )

        return super().run(fun, fun_args, fun_kwargs, secure, **kwargs)

    # TODO TEST EOS-8473
    def ensure_access(
        self, targets: Optional[List] = None, bootstrap_roster_file=None
    ):
        if not targets:
            targets = self.roster_targets()

        for target in targets:
            try:
                # try to reach using default (class-level) settings
                logger.debug(f"Checking access to '{target}'")
                self.run(
                    'uname',
                    targets=target,
                    raw_shell=True
                )
            except SaltCmdResultError as exc:
                reason = exc.reason.get(target)
                roster_file = exc.cmd_args.get('kw').get('roster_file')

                if roster_file and ('Permission denied' in reason):
                    roster = utils.load_yaml(roster_file)

                    priv_key = Path(roster.get(target, {}).get('priv'))

                    self._add_file_roots([priv_key.parent])

                    logger.debug(f"Copying access key to '{target}'")
                    if bootstrap_roster_file:
                        # NOTE assumptions:
                        #   - python3 is already there since it can be
                        #     installed using the bootstrap key
                        #     (so salt modules might be used now)
                        #   - bootstrap key is availble in salt-ssh file roots
                        #   - access key is availble in salt-ssh file roots

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
                                source=f"salt://{priv_key.name}.pub"
                            ),
                            targets=target,
                            roster_file=bootstrap_roster_file
                        )
                    else:
                        copy_id(
                            host=roster.get(target, {}).get('host'),
                            user=roster.get(target, {}).get('user'),
                            port=roster.get(target, {}).get('port'),
                            priv_key_path=priv_key,
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
        targets: Optional[List] = None,
        roster_file=None
    ):
        if not targets:
            targets = self.roster_targets()

        for target in targets:
            logger.debug(f"Ensuring python3 is installed on '{target}'")
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
                    logger.debug(f"Installing python3 on '{target}'")
                    self.run(
                        'yum install -y python3',
                        targets=target,
                        roster_file=roster_file,
                        ssh_options=exc.cmd_args.get('kw').get('ssh_options'),
                        raw_shell=True
                    )
                else:
                    raise

    @staticmethod
    def build_roster(
        nodes: List[Node], priv_key, roster_path
    ):
        roster = {
            node.minion_id: {
                'host': node.host,
                'user': node.user,
                'port': node.port,
                'priv': str(priv_key)
            } for node in nodes
        }
        utils.dump_yaml(roster_path, roster)

    # TODO TEST EOS-8473
    def ensure_ready(
            self,
            targets: Optional[List] = None,
            bootstrap_roster_file: Optional[Path] = None,
    ):
        if not targets:
            targets = self.roster_targets()

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
