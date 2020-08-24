#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

from typing import List, Dict, Type, Optional, Iterable
import logging
import uuid
from pathlib import Path

from .. import (
    inputs,
    config,
    profile,
    utils
)
from ..vendor import attr
from ..errors import (
    ProvisionerError,
    SaltCmdResultError,
)
from ..config import (
    ALL_MINIONS,
)
from ..pillar import PillarUpdater
# TODO IMPROVE EOS-8473
from ..utils import (
    load_yaml,
    dump_yaml,
    load_yaml_str,
    repo_tgz,
    run_subprocess_cmd
)
from ..ssh import keygen
from ..salt import SaltSSHClient

from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)

add_pi_merge_prefix = PillarUpdater.add_merge_prefix


# TODO TEST EOS-8473
# TODO IMPROVE EOS-8473 converters and validators
@attr.s(auto_attribs=True)
class NodeGrains:
    fqdn: str = None
    host: str = None
    ipv4: List = attr.Factory(list)
    fqdns: List = attr.Factory(list)
    not_used: Dict = attr.Factory(dict)

    @classmethod
    def from_grains(cls, **kwargs):
        # Note. assumtion that 'not_used' doesn't appear in grains
        not_used = {
            k: kwargs.pop(k) for k in list(kwargs)
            if k not in attr.fields_dict(cls)
        }
        return cls(**kwargs, not_used=not_used)

    @property
    def addrs(self):
        res = []
        for _attr in ('host', 'fqdn', 'fqdns', 'ipv4'):
            v = getattr(self, _attr)
            if v:
                if type(v) is list:
                    res.extend(v)
                else:  # str is expected
                    res.append(v)
        return list(set(res))


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class Node:
    minion_id: str
    host: str
    user: str = 'root'
    port: int = 22

    grains: Optional[NodeGrains] = None
    # ordered by priority
    _ping_addrs: List = attr.Factory(list)

    @classmethod
    def from_spec(cls, spec: str) -> 'Node':
        kwargs = {}

        parts = spec.split(':')
        kwargs['minion_id'] = parts[0]
        hostspec = parts[1]

        try:
            kwargs['port'] = parts[2]
        except IndexError:
            pass

        parts = hostspec.split('@')
        try:
            kwargs['user'] = parts[0]
            kwargs['host'] = parts[1]
        except IndexError:
            del kwargs['user']
            kwargs['host'] = parts[0]

        return cls(**kwargs)

    def __str__(self):
        return (
            '{}:{}@{}:{}'
            .format(
                self.minion_id,
                self.user,
                self.host,
                self.port
            )
        )

    @property
    def addrs(self):
        return list(set([self.host] + self.grains.addrs))

    @property
    def ping_addrs(self):
        return self._ping_addrs

    @ping_addrs.setter
    def ping_addrs(self, addrs: Iterable):
        # TODO IMPROVE EOS-8473 more effective way to order
        #      w.g. use dict (it remembers the order) and set intersection
        priorities = [
            self.grains.fqdn
        ] + self.grains.fqdns + [
            self.host,
            self.grains.host
        ] + self.grains.ipv4

        self._ping_addrs[:] = []
        for addr in priorities:
            if addr in addrs and (addr not in self._ping_addrs):
                self._ping_addrs.append(addr)

        for addr in addrs:
            if addr not in self._ping_addrs:
                self._ping_addrs.append(addr)


# TODO TEST EOS-8473
class RunArgsSetup:
    config_path: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "config.ini file path to update salt data "
                ),
            }
        },
        default=None
    )
    name: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "A name to assign to the setup profile, "
                    "auto-generated by default"
                ),
            }
        },
        default=None
    )
    profile: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "the path to the setup profile directory, "
                    "auto-generated inside current directory "
                    "by default, if specified '--name' option is ignored"
                )
            }
        },
        default=None,
        converter=(lambda v: Path(str(v)) if v else v)
    )
    prvsnr_verion: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Provisioner version to setup",
            }
        },
        default=None
    )
    source: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "the source for provisioner repo installation",
                'choices': ['local', 'gitrepo', 'rpm', 'iso']
            }
        },
        default='rpm'
    )
    # TODO EOS-12076 validate it is a dir
    local_repo: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "the path to local provisioner repo",
                'metavar': 'PATH'
            }
        },
        default=config.PROJECT_PATH,
        converter=(lambda v: Path(str(v)) if v else v),
        validator=utils.validator_path_exists
    )
    # TODO EOS-12076 validate it is a file
    iso_cortx: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "the path to a CORTX ISO",
                'metavar': 'PATH'
            }
        },
        default=None,
        converter=(lambda v: Path(str(v)) if v else v),
        validator=utils.validator_path_exists
    )
    # TODO EOS-12076 validate it is a file
    iso_cortx_deps: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "the path to a CORTX dependencies ISO",
                'metavar': 'PATH'
            }
        },
        default=None,
        converter=(lambda v: Path(str(v)) if v else v),
        validator=utils.validator_path_exists
    )
    target_build: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "Cortex integration release version repo URL/path"
                    "E.g. "
                ),
                # 'help': (
                #     "Cortex integration release version relative to "
                #     f"{config.CORTX_REPOS_BASE_URL}"
                # ),
            }
        },
        default='http://cortx-storage.colo.seagate.com/releases/eos/github/release/rhel-7.7.1908/last_successful/'  # noqa: E501
        # default='github/release/rhel-7.7.1908/last_successful',
        # converter=(lambda v: f'{config.CORTX_REPOS_BASE_URL}/{v}')
    )
    ha: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "turn on high availbility setup",
            }
        },
        default=False
    )
    field_setup: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "turn on field setup mode",
            }
        },
        default=False
    )
    salt_master: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "domain name or IP of the salt master"
            }
        },
        default=None
    )
    update: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "update initial configuration",
            }
        },
        default=False
    )
    rediscover: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "update host related configuration and connections",
            }
        },
        default=False
    )


# TODO TEST EOS-8473
@attr.s(auto_attribs=True)
class RunArgsSetupProvisionerBase:
    config_path: str = RunArgsSetup.config_path
    name: str = RunArgsSetup.name
    profile: str = RunArgsSetup.profile
    source: str = RunArgsSetup.source
    prvsnr_verion: str = RunArgsSetup.prvsnr_verion
    local_repo: str = RunArgsSetup.local_repo
    iso_cortx: str = RunArgsSetup.iso_cortx
    iso_cortx_deps: str = RunArgsSetup.iso_cortx_deps
    target_build: str = RunArgsSetup.target_build
    salt_master: str = RunArgsSetup.salt_master
    update: bool = RunArgsSetup.update
    rediscover: bool = RunArgsSetup.rediscover
    field_setup: bool = RunArgsSetup.field_setup


@attr.s(auto_attribs=True)
class RunArgsSetupProvisionerGeneric(RunArgsSetupProvisionerBase):
    ha: bool = RunArgsSetup.ha
    nodes: str = attr.ib(
        kw_only=True,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "cluster node specification, "
                    "format: id:[user@]hostname[:port]"
                ),
                'nargs': '+'
            }
        },
        converter=(
            lambda specs: [
                (s if isinstance(s, Node) else Node.from_spec(s))
                for s in specs
            ]
        )
    )

    @property
    def primary(self):
        return self.nodes[0]

    @property
    def secondaries(self):
        return self.nodes[1:]

    def __attrs_post_init__(self):
        if self.source == 'local':
            if not self.local_repo:
                raise ValueError("local repo is undefined")
        elif self.source == 'iso':
            if not self.iso_cortx:
                raise ValueError("ISO for CORTX is undefined")
            if self.iso_cortx.suffix != '.iso':
                raise ValueError("ISO extension is expected for CORTX repo")
            if not self.iso_cortx_deps:
                raise ValueError("ISO for CORTX dependencies is undefined")
            if self.iso_cortx_deps.suffix != '.iso':
                raise ValueError(
                    "ISO extension is expected for CORTX deps repo"
                )
            if self.iso_cortx.name == self.iso_cortx_deps.name:
                raise ValueError(
                    f"ISO files for CORTX and CORTX dependnecies "
                    "have the same name: {self.iso_cortx.name}"
                )


@attr.s(auto_attribs=True)
class SetupCtx:
    run_args: RunArgsSetupProvisionerGeneric
    profile_paths: Dict
    ssh_client: SaltSSHClient


# TODO TEST EOS-8473
# TODO DOC highlights
#   - multiple setups support
#   - idempotence: might be run multiple times,
#       re-tries much faster (2-3 times)
#   - multi-master initial support:
#       - list of masters is auto-generated
#         (each to each reachability is checked)
#   - parallel setup of multiple nodes
#   - paswordless ssh setup to nodes is supported
@attr.s(auto_attribs=True)
class SetupProvisioner(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSetupProvisionerGeneric

    def _resolve_grains(self, nodes: List[Node], ssh_client):
        salt_ret = ssh_client.run('grains.items')
        for node in nodes:
            # assume that list of nodes matches the result
            # TODO IMPROVE EOS-8473 better parser for grains return
            node.grains = NodeGrains.from_grains(
                **salt_ret[node.minion_id]['return']
            )

    def _prepare_roster(self, nodes: List[Node], profile_paths):
        roster = {
            node.minion_id: {
                'host': node.host,
                'user': node.user,
                'port': node.port,
                'priv': str(profile_paths['setup_key_file'])
            } for node in nodes
        }
        dump_yaml(profile_paths['salt_roster_file'], roster)

    def _create_ssh_client(self, c_path, roster_file):
        # TODO IMPROVE EOS-8473 optional support for known hosts
        ssh_options = [
            'UserKnownHostsFile=/dev/null',
            'StrictHostKeyChecking=no'
        ]
        return SaltSSHClient(
            c_path=c_path,
            roster_file=roster_file,
            ssh_options=ssh_options
        )

    def _resolve_connections(self, nodes: List[Node], ssh_client):
        addrs = {}

        for node in nodes:
            addrs[node.minion_id] = set(
                [
                    v for v in node.addrs
                    if v not in (config.LOCALHOST_IP, config.LOCALHOST_DOMAIN)
                ]
            )

        for node in nodes:
            pings = set()
            candidates = set(addrs[node.minion_id])
            for _node in nodes:
                if _node is not node:
                    candidates -= addrs[_node.minion_id]

            targets = '|'.join(
                [_node.minion_id for _node in nodes if _node is not node]
            )

            for addr in candidates:
                try:
                    ssh_client.cmd_run(
                        f"ping -c 1 -W 1 {addr}", targets=targets,
                        tgt_type='pcre'
                    )
                except SaltCmdResultError as exc:
                    logger.debug(
                        f"Possible address '{addr}' "
                        f"of {node.minion_id} is not reachable "
                        f"from some nodes: {exc}"
                    )
                else:
                    pings.add(addr)

            if pings:
                logger.info(
                    f"{node.minion_id} is reachable "
                    f"from other nodes by: {pings}"
                )
            else:
                raise ProvisionerError(
                    f"{node.minion_id} is not reachable"
                    f"from other nodes by any of {candidates}"
                )

            node.ping_addrs = list(pings)

    def _prepare_salt_masters(self, run_args):
        res = {}

        # TODO IMPROVE EOS-8473 hardcoded
        if len(run_args.nodes) == 1:
            res[run_args.nodes[0].minion_id] = [
                run_args.salt_master if run_args.salt_master
                else config.LOCALHOST_IP
            ]
            return res

        if not run_args.salt_master:
            master_nodes = (
                run_args.nodes if run_args.ha else [run_args.primary]
            )
            masters = {
                node.minion_id: node.ping_addrs[0]
                for node in master_nodes
            }
            for node in run_args.nodes:
                res[node.minion_id] = []
                for _node in run_args.nodes:
                    # not any node may be a master
                    if _node.minion_id in masters:
                        res[node.minion_id].append(
                            config.LOCALHOST_IP if _node is node
                            else masters[_node.minion_id]
                        )
        else:
            res = {
                node.minion_id: [run_args.salt_master]
                for node in run_args.nodes
            }

        return res

    def _prepare_local_repo(self, run_args, repo_dir: Path):
        # ensure parent dirs exists in profile file root
        run_subprocess_cmd(['rm', '-rf', str(repo_dir)])
        repo_dir.mkdir(parents=True, exist_ok=True)

        # (locally) prepare tgz
        repo_tgz_path = repo_dir.parent / 'repo.tgz'
        repo_tgz(
            repo_tgz_path,
            project_path=run_args.local_repo,
            version=run_args.prvsnr_verion,
            include_dirs=['pillar', 'srv', 'files', 'api', 'cli']
        )

        # extract archive locally
        run_subprocess_cmd(
            ['tar', '-zxf', str(repo_tgz_path), '-C', str(repo_dir)]
        )

        # TODO IMPROVE use salt caller and file-managed instead
        # set proper cluster.sls from template
        cluster_sls_sample_path = (
            repo_dir / 'pillar/components/samples/dualnode.cluster.sls'
        )
        cluster_sls_path = repo_dir / 'pillar/components/cluster.sls'
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(cluster_sls_sample_path),
                str(cluster_sls_path)
            ]
        )
        repo_tgz_path.unlink()

    def _copy_config_ini(self, run_args, profile_paths):
        minions_dir = (
            profile_paths['salt_fileroot_dir'] /
            "provisioner/files/minions/all/"
        )
        config_path = minions_dir / 'config.ini'
        if run_args.config_path:
            run_subprocess_cmd(
                [
                    'cp', '-f',
                    str(run_args.config_path),
                    str(config_path)
                ]
            )

    def _prepare_salt_config(self, run_args, ssh_client, profile_paths):  # noqa: E501, C901 FIXME
        minions_dir = (
            profile_paths['salt_fileroot_dir'] / "provisioner/files/minions"
        )
        all_minions_dir = minions_dir / 'all'
        master_pki_dir = (
            profile_paths['salt_fileroot_dir'] / "provisioner/files/master/pki"
        )
        master_minions_pki_dir = (
            profile_paths['salt_fileroot_dir'] /
            "provisioner/files/master/pki/minions"
        )
        pillar_all_dir = profile_paths['salt_pillar_dir'] / 'groups/all'

        #   ensure parent dirs exists in profile file root
        for path in (all_minions_dir, master_minions_pki_dir, pillar_all_dir):
            path.mkdir(parents=True, exist_ok=True)

        priv_key_path = all_minions_dir / 'id_rsa_prvsnr'
        pub_key_path = all_minions_dir / 'id_rsa_prvsnr.pub'
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(profile_paths['setup_key_file']),
                str(priv_key_path)
            ]
        )
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(profile_paths['setup_key_pub_file']),
                str(pub_key_path)
            ]
        )

        conns_pillar_path = add_pi_merge_prefix(
            pillar_all_dir / 'connections.sls'
        )
        if run_args.rediscover or not conns_pillar_path.exists():
            self._resolve_connections(run_args.nodes, ssh_client)
            conns = {
                node.minion_id: node.ping_addrs for node in run_args.nodes
            }
            dump_yaml(conns_pillar_path,  dict(connections=conns))
        else:
            conns = load_yaml(conns_pillar_path)['connections']
            for node in run_args.nodes:
                node.ping_addrs = conns[node.minion_id]

        # IMRPOVE EOS-8473 it's not a salt minion config thing
        specs_pillar_path = add_pi_merge_prefix(
            pillar_all_dir / 'node_specs.sls'
        )
        if run_args.rediscover or not specs_pillar_path.exists():
            specs = {
                node.minion_id: {
                    'user': 'root',
                    'host': node.ping_addrs[0],
                    'port': node.port
                }
                for node in run_args.nodes
            }
            dump_yaml(specs_pillar_path,  dict(node_specs=specs))

        # resolve salt masters
        # TODO IMPROVE EOS-8473 option to re-build masters
        masters_pillar_path = add_pi_merge_prefix(
            pillar_all_dir / 'masters.sls'
        )
        if run_args.rediscover or not masters_pillar_path.exists():
            masters = self._prepare_salt_masters(run_args)
            logger.info(
                f"salt masters would be set as follows: {masters}"
            )
            dump_yaml(masters_pillar_path,  dict(masters=masters))

        cluster_id_path = all_minions_dir / 'cluster_id'
        if not cluster_id_path.exists():
            cluster_uuid = uuid.uuid4()
            dump_yaml(cluster_id_path, dict(cluster_id=str(cluster_uuid)))

        #   TODO IMPROVE EOS-8473 use salt caller and file-managed instead
        #   (locally) prepare minion config
        #   FIXME not valid for non 'local' source

        # TODO IMPROVE condiition to verify local_repo
        # local_repo would be set from config.PROJECTPATH as default if not
        # specified as an argument and config.PROJECT could be None
        # if repo not found.
        if not run_args.local_repo:
            raise ValueError("local repo is undefined")

        minion_cfg_sample_path = (
            run_args.local_repo /
            'srv/components/provisioner/salt_minion/files/minion'
        )
        minion_cfg_path = all_minions_dir / 'minion'
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(minion_cfg_sample_path),
                str(minion_cfg_path)
            ]
        )
        run_subprocess_cmd(
            [
                'sed', '-i',
                "s/^master: .*/master: {{ pillar['masters'][grains['id']] }}/g",  # noqa: E501
                str(minion_cfg_path)
            ]
        )

        #   preseed master keys
        # TODO IMPROVE review, check the alternatives as more secure ways
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster_pki.html  # noqa: E501
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html  # noqa: E501
        master_key_pem = master_pki_dir / 'master.pem'
        master_key_pub = master_pki_dir / 'master.pub'
        if not (master_key_pem.exists() and master_key_pub.exists()):
            run_subprocess_cmd(
                [
                    'salt-key',
                    '--gen-keys', master_key_pem.stem,
                    '--gen-keys-dir', str(master_pki_dir)
                ]
            )

        for node in run_args.nodes:
            node_dir = minions_dir / f"{node.minion_id}"
            node_pki_dir = node_dir / 'pki'

            #   ensure parent dirs exists in profile file root
            node_pki_dir.mkdir(parents=True, exist_ok=True)

            #   TODO IMPROVE use salt caller and file-managed instead
            #   (locally) prepare minion grains
            #   FIXME not valid for non 'local' source
            minion_grains_sample_path = (
                run_args.local_repo / (
                    "srv/components/provisioner/salt_minion/files/grains.{}"
                    .format(
                        'primary' if node is run_args.primary else 'secondary'
                    )
                )
            )
            minion_grains_path = node_dir / 'grains'
            run_subprocess_cmd(
                [
                    'cp', '-f',
                    str(minion_grains_sample_path),
                    str(minion_grains_path)
                ]
            )

            #   TODO IMPROVE use salt caller and file-managed instead
            #   (locally) prepare minion node_id
            minion_nodeid_path = node_dir / 'node_id'
            if not minion_nodeid_path.exists():
                node_uuid = uuid.uuid4()
                dump_yaml(minion_nodeid_path, dict(node_id=str(node_uuid)))

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
                status = load_yaml_str(res[node.minion_id])
                dump_yaml(
                    minion_hostname_status_path,
                    dict(hostname_status=status)
                )

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
                    str(master_minions_pki_dir / node.minion_id)
                ]
            )

    def _prepare_cortx_repo_pillar(
        self, profile_paths, repos_data: Dict
    ):
        pillar_all_dir = profile_paths['salt_pillar_dir'] / 'groups/all'
        pillar_all_dir.mkdir(parents=True, exist_ok=True)

        pillar_path = add_pi_merge_prefix(
            pillar_all_dir / 'release.sls'
        )
        if pillar_path.exists():
            pillar = load_yaml(pillar_path)
        else:
            pillar = {
                'release': {
                    'base': {
                        'repos': repos_data
                    }
                }
            }
            dump_yaml(pillar_path,  pillar)

        return pillar

    def _clean_salt_cache(self, paths):
        run_subprocess_cmd(
            [
                'rm', '-rf',
                str(paths['salt_cache_dir'] / 'file_lists/roots/*')
            ]
        )

    def run(self, nodes, **kwargs):  # noqa: C901 FIXME
        # TODO update install repos logic (salt repo changes)
        # TODO firewall make more salt oriented
        # TODO sources: gitlab | gitrepo | rpm
        # TODO get latest tags for gitlab source

        # validation
        # TODO IMPROVE EOS-8473 make generic logic
        run_args = RunArgsSetupProvisionerGeneric(nodes=nodes, **kwargs)

        # TODO IMPROVE EOS-8473 better configuration way
        salt_logger = logging.getLogger('salt.fileclient')
        salt_logger.setLevel(logging.WARNING)

        # generate setup name
        setup_location = (
            run_args.profile.parent if run_args.profile else None
        )
        setup_name = (
            run_args.profile.name if run_args.profile else run_args.name
        )
        if not setup_name:
            setup_name = '__'.join(
                [str(node) for node in run_args.nodes]
            ).replace(':', '_')

        # PREPARE FILE & PILLAR ROOTS

        logger.info(f"Starting to build setup '{setup_name}'")

        paths = config.profile_paths(
            location=setup_location, setup_name=setup_name
        )

        add_file_roots = []
        add_pillar_roots = []
        if run_args.source == 'iso':
            add_file_roots = [
                run_args.iso_cortx.parent,
                run_args.iso_cortx_deps.parent
            ]

        profile.setup(
            paths,
            clean=run_args.update,
            add_file_roots=add_file_roots,
            add_pillar_roots=add_pillar_roots
        )

        logger.info(f"Profile location '{paths['base_dir']}'")

        priv_key_path = paths['setup_key_file']
        if not priv_key_path.exists():
            logger.info('Generating setup keys')
            keygen(priv_key_path)
        else:
            logger.info('Generating setup keys [skipped]')
        paths['setup_key_file'].chmod(0o600)

        logger.info("Generating a roster file")
        self._prepare_roster(run_args.nodes, paths)

        ssh_client = self._create_ssh_client(
            paths['salt_master_file'], paths['salt_roster_file']
        )

        setup_ctx = SetupCtx(run_args, paths, ssh_client)

        for node in run_args.nodes:
            logger.info(
                f"Ensuring '{node.minion_id}' is ready to accept commands"
            )
            ssh_client.ensure_ready([node.minion_id])

        logger.info("Resolving node grains")
        self._resolve_grains(run_args.nodes, ssh_client)

        #   TODO IMPROVE EOS-8473 hard coded
        logger.info("Preparing salt masters / minions configuration")
        self._prepare_salt_config(run_args, ssh_client, paths)

        logger.info("Copy config.ini to nodes")
        self._copy_config_ini(run_args, paths)

        # TODO IMPROVE EOS-9581 not all masters support
        master_targets = (
            ALL_MINIONS if run_args.ha else run_args.primary.minion_id
        )

        if run_args.source == 'local':
            logger.info("Preparing local repo for a setup")
            # TODO IMPROVE EOS-8473 hard coded
            self._prepare_local_repo(
                run_args, paths['salt_fileroot_dir'] / 'provisioner/files/repo'
            )
        elif run_args.source == 'iso':
            logger.info("Preparing CORTX repos pillar")
            self._prepare_cortx_repo_pillar(
                paths, {
                    'cortx': f"salt://{run_args.iso_cortx.name}",
                    'cortx_deps': f"salt://{run_args.iso_cortx_deps.name}"
                }
            )

        if run_args.ha and not run_args.field_setup:
            for path in ('srv/salt', 'srv/pillar', '.ssh'):
                _path = paths['salt_factory_profile_dir'] / path
                run_subprocess_cmd(['rm', '-rf',  str(_path)])
                _path.parent.mkdir(parents=True, exist_ok=True)
                run_subprocess_cmd(
                    [
                        'cp', '-r',
                        str(paths['base_dir'] / path),
                        str(_path.parent)
                    ]
                )

            run_subprocess_cmd([
                'rm', '-rf',
                str(
                    paths['salt_factory_profile_dir'] /
                    'srv/salt/provisioner/files/repo'
                )
            ])

        # Note. salt may fail to an issue with not yet cached sources:
        # "Recurse failed: none of the specified sources were found"
        # a workaround mentioned in https://github.com/saltstack/salt/issues/32128#issuecomment-207044948  # noqa: E501
        self._clean_salt_cache(paths)

        # APPLY CONFIGURATION

        logger.info("Installing Cortx yum repositories")
        # TODO IMPROVE DOC EOS-12076 Iso installation logic:
        #   - iso files are copied to user local file roots on all remotes
        #     (TODO consider user shared, currently glusterfs
        #      is not enough trusted)
        #   - iso is mounted to a location inside user local data
        #   - a repo file is created and pointed to the mount directory
        if run_args.source == 'iso':  # TODO EOS-12076 IMPROVE hard-coded
            # copy ISOs onto remotes and mount
            ssh_client.state_apply('cortx_iso')
        else:
            ssh_client.state_apply('cortx_repos')

        if run_args.ha:
            volumes = {
                'volume_salt_cache_jobs': {
                    'export_dir': '/srv/glusterfs/volume_salt_cache_jobs',
                    'mount_dir': '/var/cache/salt/master/jobs'
                },
                'volume_prvsnr_data': {
                    'export_dir': '/srv/glusterfs/volume_prvsnr_data',
                    'mount_dir': str(config.PRVSNR_DATA_SHARED_DIR)
                }
            }

            logger.info("Configuring glusterfs servers")
            # TODO IMPROVE ??? EOS-9581 glusterfs docs complains regardin /srv
            #      https://docs.gluster.org/en/latest/Administrator%20Guide/Brick%20Naming%20Conventions/  # noqa: E501
            glusterfs_server_pillar = {
                'glusterfs_dirs': [
                    vdata['export_dir'] for vdata in volumes.values()
                ]
            }
            ssh_client.state_apply(
                'glusterfs.server',
                targets=master_targets,
                fun_kwargs={
                    'pillar': glusterfs_server_pillar
                }
            )

            logger.info("Configuring glusterfs cluster")
            glusterfs_cluster_pillar = {
                'glusterfs_peers': [
                    node.ping_addrs[0] for node in run_args.nodes
                ],
                'glusterfs_volumes': {
                    vname: {
                        node.ping_addrs[0]: vdata['export_dir']
                        for node in run_args.nodes
                    } for vname, vdata in volumes.items()
                }
            }
            logger.debug(
                f"glusterfs cluster pillar: {glusterfs_cluster_pillar}"
            )
            # should be run only on one node
            ssh_client.state_apply(
                'glusterfs.cluster',
                targets=run_args.primary.minion_id,
                fun_kwargs={
                    'pillar': glusterfs_cluster_pillar
                }
            )

            logger.info("Configuring glusterfs clients")
            glusterfs_client_pillar = {
                'glusterfs_mounts': [
                    (
                        # Note. as explaind in glusterfs docs the server here
                        # 'is only used to fetch the gluster configuration'
                        run_args.primary.ping_addrs[0],
                        vname,
                        vdata['mount_dir']
                    ) for vname, vdata in volumes.items()
                ]
            }
            logger.debug(
                f"glusterfs client pillar: {glusterfs_client_pillar}"
            )
            # should be run only on one node
            ssh_client.state_apply(
                'glusterfs.client',
                fun_kwargs={
                    'pillar': glusterfs_client_pillar
                }
            )

            if not run_args.field_setup:
                logger.info("Copying factory data")
                ssh_client.state_apply(
                    'provisioner.factory_profile',
                    targets=run_args.primary.minion_id,
                )

        logger.info("Setting up paswordless ssh")
        ssh_client.state_apply('ssh')

        logger.info("Checking paswordless ssh")
        ssh_client.state_apply('ssh.check')

        # FIXME: Commented because execution hung at firewall configuration
        # logger.info("Configuring the firewall")
        # ssh_client.state_apply('firewall')

        logger.info("Installing SaltStack")
        ssh_client.state_apply('saltstack')

        if run_args.source == 'local':
            logger.info("Installing provisioner from a local source")
            ssh_client.state_apply('provisioner.local')
        else:
            raise NotImplementedError(
                f"{run_args.source} provisioner source is not supported yet"
            )

        #   CONFIGURE SALT
        logger.info("Configuring salt minions")
        res = ssh_client.state_apply('provisioner.configure_salt_minion')

        updated_keys = []
        # TODO IMPROVE EOS-8473
        minion_pki_state_id = 'file_|-salt_minion_pki_set_|-/etc/salt/pki/minion_|-recurse'  # noqa: E501
        for node_id, _res in res.items():
            if _res[minion_pki_state_id]['changes']:
                updated_keys.append(node_id)
        logger.debug(f'Updated salt minion keys: {updated_keys}')

        # TODO DOC how to pass inline pillar

        # TODO IMPROVE EOS-9581 log masters as well
        logger.info("Configuring salt masters")
        ssh_client.state_apply(
            'provisioner.configure_salt_master',
            targets=master_targets,
            fun_kwargs={
                'pillar': {
                    'updated_keys': updated_keys
                }
            }
        )

        # FIXME EOS-8473 not necessary for rpm setup
        logger.info("Installing provisioner API")
        ssh_client.state_apply('provisioner.api_install')

        logger.info("Starting salt minions")
        ssh_client.state_apply('provisioner.start_salt_minion')

        # TODO IMPROVE EOS-8473
        logger.info("Ensuring salt minions are ready")
        nodes_ids = [node.minion_id for node in run_args.nodes]
        ssh_client.cmd_run(
            f"python3 -c \"from provisioner import salt_minion; salt_minion.ensure_salt_minions_are_ready({nodes_ids})\"",  # noqa: E501
            targets=master_targets
        )

        # TODO IMPROVE EOS-8473 FROM THAT POINT REMOTE SALT SYSTEM IS FULLY
        #      CONFIGURED AND MIGHT BE USED INSTED OF SALT-SSH BASED CONTROL

        logger.info("Configuring provisioner logging")
        for state in [
            'components.system.prepare',
            'components.provisioner.config'
        ]:
            ssh_client.cmd_run(
                f"salt-call state.apply {state}",
                targets=master_targets
            )

        logger.info("Updating BMC IPs")
        ssh_client.cmd_run("salt-call state.apply components.misc_pkgs.ipmi")

        if run_args.target_build:
            logger.info("Updating target build pillar")
            # Note. in both cases (ha and non-ha) we need user pillar update
            # only on primary node, in case of ha it would be shared for other
            # masters
            ssh_client.cmd_run(
                (
                    '/usr/local/bin/provisioner pillar_set --fpath release.sls'
                    f' release/target_build \'"{run_args.target_build}"\''
                ), targets=run_args.primary.minion_id
            )

        return setup_ctx
