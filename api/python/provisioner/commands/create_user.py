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

import sys
from typing import List, Dict, Type, Union
from copy import deepcopy
import logging
from datetime import datetime
from pathlib import Path
import json
import yaml
import importlib

from ._basic import RunArgs, CommandParserFillerMixin, RunArgsBase
from .check import Check, SWUpdateDecisionMaker
from ..vendor import attr
from ..config import (
    ALL_MINIONS,
    PRVSNR_FILEROOT_DIR, LOCAL_MINION,
    PRVSNR_CORTX_COMPONENTS,
    PRVSNR_CLI_DIR,
    SEAGATE_USER_HOME_DIR, SEAGATE_USER_FILEROOT_DIR_TMPL,
    GroupChecks,
)
from ..pillar import (
    KeyPath,
    PillarKey,
    PillarUpdater,
    PillarResolver
)
# TODO IMPROVE EOS-8473
from ..utils import (
    load_yaml,
    dump_yaml_str,
)
from ..api_spec import api_spec
from ..salt import (
    StatesApplier,
    StateFunExecuter,
    State,
    SaltJobsRunner, function_run,
    copy_to_file_roots, cmd_run as salt_cmd_run,
    local_minion_id
)
from ..salt_minion import config_salt_minions
from .. import inputs, values

_mod = sys.modules[__name__]
logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class RunArgsUser:
    uname: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "name of the user"
            }
        }
    )
    passwd: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "password for the user"
            }
        }
    )
    group_list: list = attr.ib(
        default=[],
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "list of groups the user needs to be added to"
            }
        }
    )
    sudo: bool = attr.ib(
        default=True,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "if user would need root previeleages"
            }
        }
    )

    targets: str = RunArgs.targets



@attr.s(auto_attribs=True)
class CreateUser(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsUser

    def run(self, uname, passwd, groups_list=[], sudo=True, targets: str = ALL_MINIONS):

        if not SEAGATE_USER_HOME_DIR.exists():
            raise ValueError('/opt/seagate/users directory missing')

        logger.info(f"Creating new user: {uname}")
        home_dir = SEAGATE_USER_HOME_DIR / uname
        ssh_dir = home_dir / '.ssh'

        user_fileroots_dir = Path(
            PRVSNR_FILEROOT_DIR /
            SEAGATE_USER_FILEROOT_DIR_TMPL.format(uname=uname)
        )

        keyfile = user_fileroots_dir / f'id_rsa_{uname}'
        keyfile_pub = keyfile.with_name(f'{keyfile.name}.pub')

        # nodes = PillarKey('cluster/node_list')

        # nodelist_pillar = PillarResolver(LOCAL_MINION).get([nodes])
        # nodelist_pillar = next(iter(nodelist_pillar.values()))

        local_minion = local_minion_id()
        cluster_path = PillarKey('cluster')
        get_result = PillarResolver(local_minion).get([cluster_path])
        cluster_pillar = get_result[local_minion][cluster_path]
        nodes_list = [
            node for node in cluster_pillar.keys()
            if 'srvnode-' in node
        ]

        if (not cluster_pillar or
                cluster_pillar is values.MISSED):
            raise BadPillarDataError(
                'value for {} is not specified'.format(cluster_path.pi_key)
            )

        def _prepare_user_fileroots_dir():
            StateFunExecuter.execute(
                'file.directory',
                fun_kwargs=dict(
                    name=str(user_fileroots_dir),
                    makedirs=True
                )
            )

        def _generate_ssh_keys():
            StateFunExecuter.execute(
                'cmd.run',
                fun_kwargs=dict(
                    name=(
                        f"ssh-keygen -f {keyfile} "
                        "-q -C '' -N '' "
                        "-t rsa -b 4096 <<< y"
                    )
                )
            )
            StateFunExecuter.execute(
                'ssh_auth.present',
                fun_kwargs=dict(
                    # name param is mandetory and expects ssh key
                    # but ssh key is passed as source file hence name=None
                    name=None,
                    user=uname,
                    source=str(keyfile_pub),
                    config=str(user_fileroots_dir / 'authorized_keys')
                )
            )

        def _generate_ssh_config():
            for node in nodes_list:
                hostname = PillarKey(
                    'cluster/'+node+'/hostname'
                )

                hostname_pillar = PillarResolver(LOCAL_MINION).get([hostname])
                hostname_pillar = next(iter(hostname_pillar.values()))

                if (not hostname_pillar[hostname] or
                        hostname_pillar[hostname] is values.MISSED):
                    raise BadPillarDataError(
                        'value for {} is not specified'.format(hostname.pi_key)
                    )

                ssh_config = f'''Host {node} {hostname_pillar[hostname]}
    Hostname {hostname_pillar[hostname]}
    User {uname}
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile {ssh_dir}/{keyfile.name}
    IdentitiesOnly yes
    LogLevel ERROR
    BatchMode yes'''

                StateFunExecuter.execute(
                    'file.append',
                    fun_kwargs=dict(
                        name=str(user_fileroots_dir / 'config'),
                        text=ssh_config
                    )
                )

        def _copy_minion_nodes():
            StateFunExecuter.execute(
                'file.recurse',
                fun_kwargs=dict(
                    name=str(ssh_dir),
                    source=str(
                        'salt://' +
                        SEAGATE_USER_FILEROOT_DIR_TMPL.format(uname=uname)
                    ),
                    user=uname,
                    group=uname,
                    file_mode='600',
                    dir_mode='700'
                ),
                targets=targets
            )

        def _passwordless_ssh():
            _prepare_user_fileroots_dir()
            _generate_ssh_keys()
            _generate_ssh_config()
            _copy_minion_nodes()

        # Update PATH just as a precaution
        StateFunExecuter.execute(
            'file.blockreplace',
            fun_kwargs=dict(
                name='~/.bashrc',
                marker_start='# DO NOT EDIT: Start',
                marker_end='# DO NOT EDIT: End',
                content='export PATH=$PATH:/usr/local/bin',
                append_if_not_found=True,
                append_newline=True,
                backup=False
            ),
            targets=targets
        )

        StateFunExecuter.execute(
            'cmd.run',
            fun_kwargs=dict(
                name='source ~/.bashrc'
            ),
            targets=targets
        )

        if groups_list:
            logger.info(f"Creating a new group '{group_name}' with "
                        "limited access for csm admin users")
            StateFunExecuter.execute(
                'group.present',
                fun_kwargs=dict(
                    name=uname
                ),
                targets=targets
            )

        # Updating users/ dir permissions for graceful login
        StateFunExecuter.execute(
            'file.directory',
            fun_kwargs=dict(
                name=str(SEAGATE_USER_HOME_DIR),
                user='root',
                group='root',
                mode=755
            ),
            targets=targets
        )

        StateFunExecuter.execute(
            'file.managed',
            fun_kwargs=dict(
                name=f"/etc/sudoers.d/'{uname}'",
                contents=('## Restricted access for csm group users \n'
                          '%csm-admin   ALL = NOPASSWD: '
                          '/usr/bin/tail, '
                          '/usr/sbin/ifup, '
                          '/usr/sbin/ifdown, '
                          '/usr/sbin/ip, '
                          '/usr/sbin/subscription-manager, '
                          '/usr/bin/cat, '
                          '/usr/bin/cd, '
                          '/usr/bin/ls, '
                          '/usr/sbin/pcs, '
                          '/usr/bin/salt, '
                          '/usr/local/bin/salt, '
                          '/usr/bin/salt-call, '
                          '/bin/salt-call, '
                          '/usr/local/bin/salt-call, '
                          '/usr/bin/yum, '
                          '/usr/bin/dir, '
                          '/usr/bin/cp, '
                          '/usr/bin/systemctl, '
                          '/opt/seagate/cortx/csm/lib/cortxcli, '
                          '/usr/bin/cortxcli, '
                          '/usr/bin/provisioner, '
                          '/var/log, '
                          '/tmp, '
                          '/usr/bin/lsscsi, '
                          '/usr/sbin/mdadm, '
                          '/usr/sbin/sfdisk, '
                          '/usr/sbin/mkfs, '
                          '/usr/bin/rsync, '
                          '/bin/rsync, '
                          '/usr/sbin/smartctl, '
                          '/usr/bin/ipmitool, '
                          '/usr/bin/sspl_bundle_generate, '
                          '/usr/bin/sspl_bundle_generate, '
                          '/usr/bin/rabbitmqctl, '
                          '/usr/sbin/rabbitmqctl, '
                          '/var/lib/rabbitmq, '
                          '/var/log/rabbitmq, '
                          f'{SEAGATE_USER_HOME_DIR}, '
                          f'{PRVSNR_CLI_DIR}/factory_ops/boxing/init, '
                          f'{PRVSNR_CLI_DIR}/factory_ops/unboxing/init'),
                create=True,
                replace=True,
                user='root',
                group='root',
                mode=440
            ),
            targets=targets
        )

        StateFunExecuter.execute(
            'user.present',
            fun_kwargs=dict(
                name=uname,
                password=passwd,
                hash_password=True,
                home=str(home_dir),
                groups=groups_list
            ),
            targets=targets,
            secure=True
        )
        if sudo:
            StateFunExecuter.execute(
                'groupadd.adduser',
                fun_kwargs=dict(
                    name='sudo',
                    username=uname
                ),
                targets=targets
            )

        logger.info(
            'Setting up passwordless ssh for {uname} user on both the nodes'
            .format(
                uname=uname
            )
        )
        _passwordless_ssh()

