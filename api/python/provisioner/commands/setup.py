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
from typing import Type
import logging
import argparse
import uuid

from ..vendor import attr
from .. import (
    inputs
)
from ..cli_parser import KeyValueListAction
from ..attr_gen import attr_ib
from .glusterfs_setup import (
    RunArgsGlusterFSSetup,
    Runner as GlusterFSSetupRunner
)

from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)
_mod = sys.modules[__name__]


class _CompBase:
    name = None

    @abstractmethod
    def run(self, *args, targets=ALL_MINIONS, **kwargs):
        ...


@attr.s(auto_attribs=True)
class SetupRoster(_CompBase):
    name = 'roster'

    nodes: List[Node] = attr_ib('nodes', cli_spec='roster/nodes')
    priv_key: Path = attr_ib(
        'path_exists',
        default=config.SSH_PRIV_KEY,
        cli_spec='roster/priv_key'
    )
    roster_file: Path = attr_ib(
        'path',
        default=config.SALT_ROSTER_DEFAULT,
        cli_spec='roster/path'
    )

    @staticmethod
    def build(self, nodes: List[Node], priv_key):
        return {
            node.minion_id: {
                'host': node.host,
                'user': node.user,
                'port': node.port,
                'priv': str(priv_key)
            } for node in nodes
        }

    def run(self):
        dump_yaml(
            self.roster_file, self.build(self.nodes, self.priv_key)
        )


@attr.s(auto_attribs=True)
class SetupPillar(_CompBase):
    name = 'pillar'

    release_type: str = attr_ib(
        cli_spec='pillar/release_type',
        default=config.DistrType.BUNDLE.value,
        # TODO EOS-12076 better validation
        converter=(lambda v: config.DistrType(v))
    )
    release_deps_bundle_url: str = attr_ib(
        default=None, cli_spec='pillar/release_deps_bundle_url'
    )
    release_target_build: str = attr_ib(
        default=None, cli_spec='pillar/release_target_build'
    )
    service_user_password: str = attr_ib(
        default=None, cli_spec='pillar/service_user_password'
    )

    def __attrs_post_init__(self):
        # TODO add option to keep current value for service user
        if (
            self.service_user_password
            == config.CLI_NEW_SERVICE_USER_PWD_VALUE
        ):
            logger.info("Generating service user password")
            self.service_user_password = str(uuid.uuid4()).split('-')[0]

    def run(self):
        pillars = []

        if self.release_type:
            pillars.append(
                ('release/type', self.dist_type.value)
            )

        if self.release_deps_bundle_url:
            pillars.append(
                ('release/deps_bundle_url', self.release_deps_bundle_url)
            )

        if self.release_target_build:
            pillars.append(
                ('release/target_build', self.release_target_build)
            )

        if self.service_user_password:
            pillars.append(
                ('system/service_user/password', service_user_password)
            )

        if pillars:
            pi_updater = PillarUpdater(pillar_path=USER_SHARED_PILLAR)
            pi_updater.update(*pillars)
            pi_updater.apply()
        else:
            logger.warning('No pillar data provided')


@attr.s(auto_attribs=True)
class SetupGlusterFS(_CompBase, RunArgsGlusterFSSetup):
    name = 'glusterfs'

    def run(self):
        return GlusterFSSetupRunner(self).run()


@attr.s(auto_attribs=True)
class Connections():
    name = 'saltstack'
    ha: bool = attr_ib(cli_spec='setup/ha', default=False)
    salt_master: str = attr_ib(cli_spec='setup/salt_master', default=None)
    ssh_client: SaltSSHClient = attr.ib(init=False, default=None)

    _master_targets: str = attr.ib(init=False, default=None)

    _pillar_conns: dict = attr_ib(init=False, default=None)
    _pillar_cluster: dict = attr_ib(init=False, default=None)

    def __attrs_post_init__(self):
        self.ssh_client = SaltSSHClient()
        for node in conns_pillar:

    def pillar_connections(self, refresh=False):
        if refresh or self._pillar_conns is None:
            # resolving connections info
            pillar_resolver = PillarResolverNew(client=ssh_client)
            self._pillar_conns = pillar_resolver.get(
                [PillarKey('setup/connections')]
            )
        return self._pillar_conns

    def pillar_cluster(self, refresh=False):
        if refresh or self._pillar_cluster is None:
            # resolving cluster info
            target = client.roster_targets()[0]
            pillar_resolver = PillarResolverNew(
                targets=target, client=ssh_client
            )
            self._pillar_cluster = pillar_resolver.get(
                [PillarKey('cluster')]
            )[target]
        return self._pillar_cluster

    # TODO IMPROVE return not dict but special type for connections data
    def resolve(self, refresh=False):
        conns = self.pillar_connections(refresh=refresh)
        # TODO IMPROVE resolve only if needed
        cluster = self.pillar_cluster(refresh=refresh)

        res = {}
        for _id, _conns in conns.items():
            _res = conns['connections']
            default = _res.pop('default')

            for conn_t, conn_host_key in (
                ('ssh', 'host'), ('glusterfs', 'peer'), ('saltstack', 'master')
            ):
                if not _res[conn_t][conn_host_key]:
                    try:
                        res[conn_t][conn_host_key] = (
                            default if default
                            else cluster['cluster'][_id]['network']['data_nw']['pvt_ip_addr']
                        )
                    except KeyError:
                        _res[conn_t][conn_host_key] = None

        return res



# assumptions:
# - salt-ssh env is configured:
#   - roster file is up to date
#   - /etc/salt/master is set
#   - pillar for connections are set
@attr.s(auto_attribs=True)
class SetupSaltStack(_CompBase):
    name = 'saltstack'


    ha: bool = attr_ib(cli_spec='setup/ha', default=False)
    salt_master: str = attr_ib(cli_spec='setup/salt_master', default=None)
    ssh_client: SaltSSHClient = attr.ib(init=False, default=None)

    _master_targets: str = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        ssh_targets = self.ssh_client.roster_targets()
        self.ssh_client = SaltSSHClient()

        # resolving connections info
        pillar_resolver = PillarResolverNew(client=ssh_client)
        conns_pillar = pillar_resolver.get([PillarKey('setup/connections')])

        self._master_targets = (
            ALL_MINIONS if self.ha else ssh_targets[0]
        )

        for node in conns_pillar:

    def _prepare_salt_masters(self, conns):
        res = {}

        # TODO IMPROVE EOS-8473 hardcoded
        if len(conns) == 1:
            res[list(conns)[0]] = [
                self.salt_master if self.salt_master
                else config.LOCALHOST_IP
            ]
            return res

        if not self.salt_master:
            salt_masters = {
                node.minion_id: node.ping_addrs[0]
                for node in self._master_targets
            }
            for node in run_args.nodes:
                res[node.minion_id] = []
                for _node in run_args.nodes:
                    # note: any node may be a salt-master
                    if _node.minion_id in salt_masters:
                        res[node.minion_id].append(
                            config.LOCALHOST_IP if _node is node
                            else salt_masters[_node.minion_id]
                        )
        else:
            res = {
                node.minion_id: [self.salt_master]
                for node in run_args.nodes
            }

        return res

    # TODO IMPROVE many hard coded values
    def _set_salt_pki(self, run_args, ssh_client, paths):  # noqa: E501, C901 FIXME
        fileroot = FileRoot(USER_SHARED_FILEPATH, refresh_on_update=False)

        minions_dir = "components/provisioner/setup/files/minions"
        all_minions_dir = minions_dir / 'all'
        salt_master_pki_dir = "components/provisioner/setup/salt_master/files/pki"
        salt_master_minions_pki_dir = salt_master_pki_dir / 'minions'

        cluster_id_path = all_minions_dir / 'cluster_id'
        if not fileroot.exists(cluster_id_path):
            cluster_uuid = str(uuid.uuid4())
            fileroot.write_yaml(cluster_id_path, dict(cluster_id=cluster_uuid))
        else:
            cluster_uuid = fileroot.read_yaml(cluster_id_path)['cluster_id']

        # TODO IMPROVE review, check the alternatives as more secure ways
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster_pki.html  # noqa: E501
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html  # noqa: E501
        master_key_pem = salt_master_pki_dir / 'master.pem'
        master_key_pub = salt_master_pki_dir / 'master.pub'
        if not (
            fileroot.exists(master_key_pem)
            and fileroot.exists(master_key_pub)
        ):
            master_key_pem = fileroot.path(master_key_pem)
            master_key_pub = fileroot.path(master_key_pub)

            # FIXME violates FileRoot encapsulation
            run_subprocess_cmd(
                [
                    'salt-key',
                    '--gen-keys', master_key_pem.stem,
                    '--gen-keys-dir', str(salt_master_pki_dir)
                ]
            )

        for node in run_args.nodes:
            node_dir = minions_dir / f"{node.minion_id}"
            node_pki_dir = node_dir / 'pki'
            node_pillar_dir = pillar_minions_dir / f"{node.minion_id}"

            #   ensure parent dirs exists in profile file root
            node_pki_dir.mkdir(parents=True, exist_ok=True)
            node_pillar_dir.mkdir(parents=True, exist_ok=True)

            #   TODO IMPROVE use salt caller and file-managed instead
            #   (locally) prepare minion node_id
            minion_nodeid_path = node_dir / 'node_id'
            if not minion_nodeid_path.exists():
                node_uuid = str(uuid.uuid4())
                dump_yaml(minion_nodeid_path, dict(node_id=node_uuid))
            else:
                node_uuid = load_yaml(minion_nodeid_path)['node_id']

            # TODO IMPROVE EOS-8473 consider to move to mine data
            # (locally) prepare hostname info
            minion_hostname_status_path = node_dir / 'hostname_status'
            if run_args.rediscover or not minion_hostname_status_path.exists():
                res = ssh_client.cmd_run(
                    "hostnamectl status  | sed 's/^ *//g'",
                    fun_kwargs=dict(python_shell=True),
                    targets=node.minion_id
                )
                # Note. output here is similar to yaml format
                # ensure that it is yaml parseable
                hostnamectl_status = load_yaml_str(res[node.minion_id])
                dump_yaml(
                    minion_hostname_status_path,
                    dict(hostname_status=hostnamectl_status)
                )
            else:
                hostnamectl_status = load_yaml(
                    minion_hostname_status_path
                )['hostname_status']

            setup_pillar_path = add_pillar_merge_prefix(
                node_pillar_dir / 'setup.sls'
            )
            if run_args.rediscover or not setup_pillar_path.exists():
                data = {
                    'setup': {
                        'config': {
                            'master': masters[node.minion_id]
                        },
                        'grains': [
                            # FIXME not accurate in case of HA setup
                            {'roles': [
                                'primary' if (node is run_args.primary)
                                else 'secondary'
                            ]},
                            {'cluster_id': cluster_uuid},
                            {'node_id': node_uuid},
                            {'hostname_status': hostnamectl_status},
                        ]
                    }
                }
                dump_yaml(setup_pillar_path, data)

            #   preseed minion keys
            node_key_pem_tmp = node_pki_dir / f'{node.minion_id}.pem'
            node_key_pub_tmp = node_pki_dir / f'{node.minion_id}.pub'
            node_key_pem = node_pki_dir / 'minion.pem'
            node_key_pub = node_pki_dir / 'minion.pub'

            if not (node_key_pem.exists() and node_key_pub.exists()):
                run_subprocess_cmd(
                    [
                        'salt-key',
                        '--gen-keys', node.minion_id,
                        '--gen-keys-dir', str(node_pki_dir)
                    ]
                )
                node_key_pem_tmp.rename(node_key_pem)
                node_key_pub_tmp.rename(node_key_pub)

            run_subprocess_cmd(
                [
                    'cp', '-f',
                    str(node_key_pub),
                    str(salt_master_minions_pki_dir / node.minion_id)
                ]
            )


            fileroot.refresh()





    def run(self):
        # TODO set setup:cofig:master basing on setup:connections
        #      (or cluster...pvt_ip_addr if no data)

        logger.info("Configuring salt minions")
        res = ssh_client.state_apply('components.provisioner.setup.salt_minion')

        updated_keys = []
        # TODO IMPROVE EOS-8473
        minion_pki_state_id = 'file_|-salt_minion_pki_set_|-/etc/salt/pki/minion_|-recurse'  # noqa: E501
        for node_id, _res in res.items():
            if _res[minion_pki_state_id]['changes']:
                updated_keys.append(node_id)
        logger.debug(f'Updated salt minion keys: {updated_keys}')

        # TODO DOC how to pass inline pillar

        # TODO IMPROVE EOS-9581 log salt-masters as well
        # TODO IMPROVE salt might be restarted in the background,
        #      might require to ensure that it is ready to avoid
        #      a race condition with further commands that relies
        #      on it (e.g. salt calls and provisioner api on a remote).
        #      To consider the similar logic as in salt_master.py.
        #
        #      Alternative: pospone that step once core and API
        #      is installed and we may call that on remotes
        try:
            logger.info("Configuring salt-masters")
            ssh_client.state_apply(
                'components.provisioner.setup.salt_master',
                targets=self._master_targets,
                fun_kwargs={
                    'pillar': {
                        'updated_keys': updated_keys
                    }
                }
            )
        except SaltCmdRunError as exc:
            if 'Stream is closed' in str(exc):
                logger.warning('salt-ssh lost a stream, trying to workaround')
                # FIXME dirty code
                targets = (
                    self.ssh_client.roster_targets()
                    if self._master_targets == ALL_MINIONS
                    else [self._master_targets]
                )

                for target in targets:
                    logger.info(f"stopping salt-master on {target}")
                    ssh_client.run(
                        'cmd.run', targets=target,
                        fun_args=['systemctl stop salt-master']
                    )

                logger.info(f"Starting salt-masters on {self._master_targets}")
                ssh_client.run(
                    'cmd.run', targets=self._master_targets,
                    fun_args=['systemctl start salt-master']
                )
            else:
                raise

        logger.info("Starting salt minions")
        ssh_client.state_apply('components.provisioner.salt_minion.start')

        # TODO EOS-14019 might consider to move to right after restart
        logger.info("Ensuring salt-masters are ready")
        ssh_client.state_apply(
            'components.provisioner.salt_master.start',
            targets=self._master_targets
        )

        # TODO IMPROVE EOS-8473
        # Note. we run the same on all masters to verify each master
        #       connection to minions
        logger.info("Ensuring salt minions are ready")
        nodes_ids = [node.minion_id for node in run_args.nodes]
        ssh_client.cmd_run(
            (
                f"python3 -c \"from provisioner import salt_minion; "
                f"salt_minion.ensure_salt_minions_are_ready({nodes_ids})\""
            ),
            targets=self._master_targets
        )


@attr.s(auto_attribs=True)
class SetupCmd(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams

    components = {
        _attr.comp_name: _attr for _attr in dir(_mod)
        (
            if issubclass(_attr, _CompBase)
            and _attr.comp_name
        )
    }

    @classmethod
    def fill_parser(cls, parser, parents=None):
        if parents is None:
            parents = []

        parser_common = argparse.ArgumentParser(add_help=False)
        super().fill_parser(parser_common)

        parents.append(parser_common)

        subparsers = parser.add_subparsers(
            dest='component',
            title='components',
            description='valid components'
        )

        for cl_name, cl_t in cls.components.items():
            subparser = subparsers.add_parser(
                cl_name, description='{} configuration'.format(cl_name),
                help='{} component help'.format(cl_name), parents=parents,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
            inputs.ParserFiller.fill_parser(cl_t, subparser)

    @classmethod
    def extract_positional_args(cls, kwargs):
        comp_t = cls.components[kwargs.pop('component')]
        _args = [comp_t]

        args, kwargs = super().extract_positional_args(kwargs)
        _args.extend(args)

        args, kwargs = inputs.ParserFiller.extract_positional_args(
            comp_t, kwargs
        )
        _args.extend(args)

        return _args, kwargs

    def run(self, comp_t, fun, *args, **kwargs):
        component_kwargs = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(comp_t)
        }

        run_args = RunArgsSetupCmd(fun, **{
            k: kwargs.pop(k) for k in list(kwargs)
            if k in attr.fields_dict(RunArgsSetupCmd)
        })

        component = comp_t(*args, **component_kwargs)

        return component.run(
            run_args.fun,
            run_args.fun_args,
            run_args.fun_kwargs,
            run_args.secure,
            **(run_args.kwargs or {})
        )
