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

from typing import List, Dict, Type, Optional, Iterable
# import socket
import logging
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
    SaltCmdRunError
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
    run_subprocess_cmd,
    node_hostname_validator
)
from ..ssh import keygen
from ..salt import SaltSSHClient

from . import (
    CommandParserFillerMixin
)
from .setup_provisioner import (
    NodeGrains, Node, SetupCmdBase,
    SetupCtx, RunArgsSetupProvisionerGeneric
)


logger = logging.getLogger(__name__)

add_pillar_merge_prefix = PillarUpdater.add_merge_prefix


@attr.s(auto_attribs=True)
class _Runner:
    run_args: RunArgsSetupProvisionerGeneric
    profile: Dict = attr.ib(init=False, default=None)
    ssh_client: SaltSSHClient = attr.ib(init=False, default=None)
    pillar_path: PillarPath = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        # generate setup name
        # FIXME
        setup_location = SetupCmdBase.setup_location(run_args)
        setup_name = SetupCmdBase.setup_name(run_args)

        self.profile = config.profile_paths(
            config.profile_base_dir(
                location=setup_location, setup_name=setup_name
            )
        )

        self.ssh_client = SaltSSHClient(
            self.profile['salt_master_file'], self.profile['salt_roster_file']
        )

        self.pillar_path = PillarPath(
            self.profile['salt_pillar_dir'], PRVSNR_FACTORY_PILLAR_PREFIX.prefix
        )

    @property
    def setup_ctx(self):
        return SetupCtx(
            self.run_args, self.profile, self.ssh_client
        )


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

    def _prepare_roster(
        self, nodes: List[Node], priv_key
    ):
        return {
            node.minion_id: {
                'host': node.host,
                'user': node.user,
                'port': node.port,
                'priv': str(priv_key)
            } for node in nodes
        }

    def _resolve_connections(self, nodes: List[Node], ssh_client):
        addrs = {}

        # TODO EOS-11511 improve later
        # the problem: local hostname might appear in grains
        # (probably for VMs only)

        # local_hostname = socket.gethostname()

        for node in nodes:
            addrs[node.minion_id] = set(
                [
                    v for v in node.addrs
                    if v not in (
                        config.LOCALHOST_IP,
                        config.LOCALHOST_DOMAIN,
                        # local_hostname
                    )
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
            salt_masters = {
                node.minion_id: node.ping_addrs[0]
                for node in master_nodes
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
            version=run_args.prvsnr_version,
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

    def _copy_config_ini(self, run_args, profile):
        minions_dir = (
            profile['salt_fileroot_dir'] /
            "provisioner/files/minions/all/"
        )
        config_path = minions_dir / 'config.ini'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if run_args.config_path:
            run_subprocess_cmd(
                [
                    'cp', '-f',
                    str(run_args.config_path),
                    str(config_path)
                ]
            )

    # FIXME EOS-15022
    def _locate_setup_keys(self, profile):  # noqa: E501, C901 FIXME
        minions_dir = (
            profile['salt_fileroot_dir'] / "provisioner/files/minions"
        )
        all_minions_dir = minions_dir / 'all'
        all_minions_dir.mkdir(parents=True, exist_ok=True)

        priv_key_path = all_minions_dir / 'id_rsa_prvsnr'
        pub_key_path = all_minions_dir / 'id_rsa_prvsnr.pub'
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(profile['setup_key_file']),
                str(priv_key_path)
            ]
        )
        run_subprocess_cmd(
            [
                'cp', '-f',
                str(profile['setup_key_pub_file']),
                str(pub_key_path)
            ]
        )


    # TODO IMPROVE DRY
    def _prepare_factory_setup_pillar(
        self, profile, run_args
    ):
        # TODO IMPROVE here the setup pillar would have partial
        #      duplication of release pillar (e.g. target build)
        pillar = attr.asdict(run_args)
        # TODO IMPROVE EOS-13686 more clean way
        if pillar['dist_type']:
            pillar['dist_type'] = pillar['dist_type'].value
        if pillar['local_repo']:
            pillar['local_repo'] = str(pillar['local_repo'])
        if pillar['iso_os']:
            pillar['iso_os'] = str(config.PRVSNR_OS_ISO)
        if pillar['iso_cortx']:
            if pillar['iso_cortx_deps']:
                pillar['iso_cortx'] = str(config.PRVSNR_CORTX_ISO)
                pillar['iso_cortx_deps'] = str(
                    config.PRVSNR_CORTX_DEPS_ISO
                )
            else:
                pillar['iso_cortx'] = str(config.PRVSNR_CORTX_SINGLE_ISO)
        pillar.pop('bootstrap_key')
        return pillar

    @staticmethod
    def _generate_release_pillar(setup_ctx):
        return {
            'release': {
                'type': (
                    # TODO better types for distribution
                    'bundle'
                    if run_args.dist_type == config.DistrType.BUNDLE
                    else 'internal'
                ),
                'target_build': run_args.target_build,
                'deps_bundle_url': run_args.url_cortx_deps,
                'base': {
                    'repos': self._generate_repos_pillar(setup_ctx)
                },
                'python_repo': (
                    f"{run_args.target_build}/"
                    f"{config.CORTX_PYTHON_ISO_DIR}"
                    if not run_args.pypi_repo
                    else 'https://pypi.org/'
                )
            }
        }

    def _prepare_glusterfs_pillar(self, profile, in_docker=False):
        pillar_all_dir = profile['salt_pillar_dir'] / 'groups/all'
        pillar_all_dir.mkdir(parents=True, exist_ok=True)

        glusterfs_pillar_path = pillar_all_dir / 'glusterfs.sls'
        if glusterfs_pillar_path.exists():
            data = load_yaml(glusterfs_pillar_path)['glusterfs']
        else:
            data = {
                'in_docker': in_docker,
                'volumes': {
                    'volume_salt_cache_jobs': {
                        'export_dir': str(config.GLUSTERFS_VOLUME_SALT_JOBS),
                        'mount_dir': '/var/cache/salt/master/jobs'
                    },
                    'volume_prvsnr_data': {
                        'export_dir': str(config.GLUSTERFS_VOLUME_PRVSNR_DATA),
                        'mount_dir': str(config.PRVSNR_DATA_SHARED_DIR)
                    }
                }
            }
            dump_yaml(glusterfs_pillar_path,  dict(glusterfs=data))

        return data

    def _clean_salt_cache(self, profile):
        run_subprocess_cmd(
            [
                'rm', '-rf',
                str(profile['salt_cache_dir'] / 'file_lists/roots/*')
            ]
        )

    @staticmethod
    def _generate_repos_pillar(setup_ctx):
        profile = setup_ctx.profile
        run_args = setup_ctx.run_args
        ssh_client = setup_ctx.ssh_client

        logger.info("Preparing CORTX repos pillar")

        # FIXME rhel and centos repos
        deps_bundle_url = (
            f"{run_args.target_build}/{config.CORTX_3RD_PARTY_ISO_DIR}"
            if run_args.dist_type == config.DistrType.BUNDLE
            else run_args.url_cortx_deps
        )

        if run_args.source == 'iso':
            if run_args.iso_cortx_deps:
                repos = {
                    config.CORTX_ISO_DIR: (
                        f"salt://{run_args.iso_cortx.name}"
                    ),
                    config.CORTX_3RD_PARTY_ISO_DIR: (
                        f"salt://{run_args.iso_cortx_deps.name}"
                    )
                }
            else:
                logger.info("... NOTE: single ISO mode would be set")
                repos = {
                    config.CORTX_SINGLE_ISO_DIR: {
                        'source': f"salt://{run_args.iso_cortx.name}",
                        'is_repo': False
                    },
                    config.CORTX_ISO_DIR: (
                        f"{run_args.target_build}/{config.CORTX_ISO_DIR}"
                    ),
                    config.CORTX_3RD_PARTY_ISO_DIR: deps_bundle_url
                }

            if run_args.iso_os:
                repos[config.OS_ISO_DIR] = f"salt://{run_args.iso_os.name}"

        elif run_args.source == 'rpm':
            if run_args.dist_type == config.DistrType.BUNDLE:
                repos = {
                    config.CORTX_ISO_DIR: (
                        f"{run_args.target_build}/cortx_iso"
                    ),
                    config.CORTX_3RD_PARTY_ISO_DIR: deps_bundle_url
                }
            else:
                repos = {
                    config.CORTX_ISO_DIR: f'{run_args.target_build}'
                }
                if deps_bundle_url:
                    repos[config.CORTX_3RD_PARTY_ISO_DIR] = deps_bundle_url
        else:
            raise ValueError(f"unexpected source '{run_args.source}' here")

        # assume that target_build for bundled release is
        # a base dir for bundle distribution

        if deps_bundle_url and False:
            repos.update({
                '3rd_party_epel': (
                    f"{deps_bundle_url}/EPEL-7"
                ),
                '3rd_party_saltstack': (
                    f"{deps_bundle_url}/commons/saltstack-3001"
                ),
                '3rd_party_glusterfs': (
                    f"{deps_bundle_url}/commons/glusterfs"
                )
            })

        return repos

    @staticmethod
    def _generate_profile(profile, run_args):
        add_file_roots = []
        add_pillar_roots = []
        if run_args.source == 'iso':
            add_file_roots = [
                run_args.iso_cortx.parent,
            ]
            if run_args.iso_os:
                add_file_roots.append(run_args.iso_os.parent)
            if run_args.iso_cortx_deps:
                add_file_roots.append(run_args.iso_cortx_deps.parent)

        if run_args.bootstrap_key:
            add_file_roots = [
                run_args.bootstrap_key.parent
            ]

        profile.setup(
            profile,
            clean=run_args.update,
            add_file_roots=add_file_roots,
            add_pillar_roots=add_pillar_roots
        )

    @staticmethod
    def _generate_pillar(setup_ctx: SetupCtx):
        profile = setup_ctx.profile
        run_args = setup_ctx.run_args
        ssh_client = setup_ctx.ssh_client
        pillars = []

        logger.info("Preparing setup pillar")
        pillars.append((
            'factory_setup', self._prepare_factory_setup_pillar(
                profile, run_args
            )
        ))

        logger.info("Generating a roster file")
        SetupRoster(
            run_args.nodes,
            profile['setup_key_file'],
            profile['salt_roster_file']
        ).run()

        if run_args.bootstrap_key:
            SetupRoster(
                run_args.nodes,
                run_args.bootstrap_key,
                profile['salt_bootstrap_roster_file']
            ).run()

        # FIXME what about local: it requires some sources
        #       for non provisioner pkgs
        if run_args.source in ('iso', 'rpm'):
            pillars.append((
                'release', self._generate_release_pillar(setup_ctx)
            ))

        pi_updater = PillarUpdater(pillar_path=self._pillar_path)
        pi_updater.update(*pillars)
        pi_updater.apply()


    def _prepare_profile()
        # PREPARE FILE & PILLAR ROOTS
        logger.info(f"Starting to build setup '{setup_name}'")

        self._generate_profile(profile, run_args)

        logger.info(f"Profile location '{profile['base_dir']}'")

        logger.info("Copying config.ini to file root")
        self._copy_config_ini(run_args, profile)

        priv_key_path = profile['setup_key_file']
        if not priv_key_path.exists():
            logger.info('Generating setup keys')
            keygen(priv_key_path)
            self._locate_setup_keys(profile)
        else:
            logger.info('Generating setup keys [skipped]')
        profile['setup_key_file'].chmod(0o600)

        logger.info("Generating factory pillars")
        self._generate_pillar(setup_ctx)

        logger.info("Preparing factory profile")
        for path in ('srv/salt', 'srv/pillar', '.ssh'):
            _path = profile['salt_factory_profile_dir'] / path
            run_subprocess_cmd(['rm', '-rf',  str(_path)])
            _path.parent.mkdir(parents=True, exist_ok=True)
            run_subprocess_cmd(
                [
                    'cp', '-r',
                    str(profile['base_dir'] / path),
                    str(_path.parent)
                ]
            )

        run_subprocess_cmd([
            'rm', '-rf',
            str(
                profile['salt_factory_profile_dir'] /
                'srv/salt/provisioner/files/repo'
            )
        ])

    def _ensure_access(self):
        for node in run_args.nodes:
            logger.info(
                f"Ensuring '{node.minion_id}' is ready to accept commands"
            )
            ssh_client.ensure_ready(
                [node.minion_id],
                bootstrap_roster_file=(
                    profile['salt_bootstrap_roster_file']
                    if profile['salt_bootstrap_roster_file'].exists()
                    else None
                )
            )

    def _resolve_grains(self, nodes: List[Node], ssh_client):
        logger.info("Resolving node grains")
        salt_ret = ssh_client.run('grains.items')
        for node in nodes:
            # assume that list of nodes matches the result
            # TODO IMPROVE EOS-8473 better parser for grains return
            node.grains = NodeGrains.from_grains(
                **salt_ret[node.minion_id]['return']
            )

    def _config_passwordless_ssh(self):
        try:
            logger.info("Checking paswordless ssh")
            ssh_client.state_apply('ssh.check')
        except SaltCmdResultError:
            logger.info("Setting up paswordless ssh")
            ssh_client.state_apply('ssh')
            logger.info("Checking paswordless ssh")
            ssh_client.state_apply('ssh.check')

    def _setup_repos(self):
        logger.info("Installing Cortx yum repositories")
        # TODO IMPROVE DOC EOS-12076 Iso installation logic:
        #   - iso files are copied to user local file roots on all remotes
        #     (TODO consider user shared, currently glusterfs
        #      is not enough trusted)
        #   - iso is mounted to a location inside user local data
        #   - a repo file is created and pointed to the mount directory
        # TODO EOS-12076 IMPROVE hard-coded
        if run_args.source in ('iso', 'rpm'):
            # do not copy ISO for the node where we are now already
            if (
                run_args.field_setup
                and run_args.source == 'iso'
                and (
                    not run_args.iso_os
                    or run_args.iso_os == config.PRVSNR_OS_ISO
                )
                and (
                    run_args.iso_cortx == config.PRVSNR_CORTX_SINGLE_ISO
                    or (
                        run_args.iso_cortx == config.PRVSNR_CORTX_ISO and
                        run_args.iso_cortx_deps == config.PRVSNR_CORTX_DEPS_ISO
                    )
                )
            ):
                # FIXME it is valid only for replace_node logic,
                #       not good to rely on some specific case here
                # FIXME hardcoded pillar key
                ssh_client.state_apply(
                    'repos', targets=run_args.primary.minion_id,
                    fun_kwargs={
                        'pillar': {
                            'skip_iso_copy': True
                        }
                    }
                )
                # NOTE for now salt-ssh supports only glob and regex targetting
                # https://docs.saltstack.com/en/latest/topics/ssh/#targeting-with-salt-ssh
                ssh_client.state_apply(
                    'repos',
                    targets='|'.join([
                        node.minion_id for node in run_args.secondaries
                    ]),
                    tgt_type='pcre'
                )
            else:
                # copy ISOs onto all remotes and mount
                ssh_client.state_apply('repos')

            ssh_client.state_apply('cortx_repos')  # FIXME EOS-12076
        else:
            ssh_client.state_apply('cortx_repos')

        if not run_args.pypi_repo:
            logger.info("Setting up custom python repository")
            ssh_client.state_apply('repos.pip_config')

    def _install_saltstack(self):
        logger.info("Installing SaltStack")
        ssh_client.state_apply('saltstack')

    def _install_provisioner(self):
        logger.info(
            f"Installing provisioner from a '{run_args.source}' source"
        )
        if run_args.source in ('iso', 'rpm'):
            ssh_client.state_apply('provisioner.install')
        elif run_args.source == 'local':
            ssh_client.state_apply('provisioner.install.local')
        else:
            raise NotImplementedError(
                f"{run_args.source} provisioner source is not supported yet"
            )

    def _install_provisioner_api(self):
        logger.info("Installing provisioner API")
        ssh_client.state_apply(
            'provisioner.api.install',
            fun_kwargs={
                'pillar': {
                    'api_distr': (
                        'pip' if run_args.source == 'local' else 'pkg'
                    )
                }
            }
        )

    def _prepare_salt_config(self, run_args, ssh_client, paths):  # noqa: E501, C901 FIXME
        minions_dir = (
            paths['salt_fileroot_dir'] / "provisioner/files/minions"
        )
        all_minions_dir = minions_dir / 'all'
        salt_master_pki_dir = (
            paths['salt_fileroot_dir'] / "provisioner/files/master/pki"
        )
        salt_master_minions_pki_dir = (
            paths['salt_fileroot_dir'] /
            "provisioner/files/master/pki/minions"
        )
        pillar_all_dir = paths['salt_pillar_dir'] / 'groups/all'
        pillar_minions_dir = paths['salt_pillar_dir'] / 'minions'

        #   ensure parent dirs exists in profile file root
        for path in (
            all_minions_dir,
            salt_master_minions_pki_dir,
            pillar_all_dir,
            pillar_minions_dir
        ):
            path.mkdir(parents=True, exist_ok=True)

        conns_pillar_path = add_pillar_merge_prefix(
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
        specs_pillar_path = add_pillar_merge_prefix(
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

        # resolve salt-masters
        # TODO IMPROVE EOS-8473 option to re-build masters
        masters_pillar_path = add_pillar_merge_prefix(
            pillar_all_dir / 'masters.sls'
        )
        if run_args.rediscover or not masters_pillar_path.exists():
            masters = self._prepare_salt_masters(run_args)
            logger.info(
                f"salt-masters would be set as follows: {masters}"
            )
            dump_yaml(masters_pillar_path,  dict(masters=masters))
        else:
            masters = load_yaml(masters_pillar_path)

        # TODO IMPROVE many hard coded values

        cluster_id_path = all_minions_dir / 'cluster_id'
        if not cluster_id_path.exists():
            cluster_uuid = str(uuid.uuid4())
            dump_yaml(cluster_id_path, dict(cluster_id=cluster_uuid))
        else:
            cluster_uuid = load_yaml(cluster_id_path)['cluster_id']

        #   TODO IMPROVE EOS-8473 use salt caller and file-managed instead
        #   (locally) prepare minion config
        #   FIXME not valid for non 'local' source

        # TODO IMPROVE review, check the alternatives as more secure ways
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster_pki.html  # noqa: E501
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html  # noqa: E501
        master_key_pem = salt_master_pki_dir / 'master.pem'
        master_key_pub = salt_master_pki_dir / 'master.pub'
        if not (master_key_pem.exists() and master_key_pub.exists()):
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


    def prepare(self):
        if not run_args.field_setup:
            self._prepare_profile()

        self._ensure_access()

        # TODO EOS-15022 might be not needed anymore
        if not run_args.field_setup:
            logger.info("Copying factory data")
            ssh_client.state_apply(
                'provisioner.factory_profile',
                targets=run_args.primary.minion_id,
            )

        self._resolve_grains()

        self._setup_repos()

    def install(self):

        self._install_saltstack()

        self._install_provisioner()

        self._install_provisioner_api()

    def config(self):
        #   TODO IMPROVE EOS-8473 hard coded
        logger.info("Preparing saltstack configuration")
        self._prepare_salt_config(run_args, ssh_client, profile)  # UPDATE

        # Note. salt may fail to an issue with not yet cached sources:
        # "Recurse failed: none of the specified sources were found"
        # a workaround mentioned in https://github.com/saltstack/salt/issues/32128#issuecomment-207044948  # noqa: E501
        self._clean_salt_cache(profile)  # UPDATE

        logger.info("Preparing env for salt-ssh on a primary node")
        ssh_client.run(
            'state.sls',
            fun_args=[
                'salt_master_configured',
                'components.provisioner.setup.salt_master'
            ],
            targets=run_args.primary.minion_id
        )

        self._config_passwordless_ssh()  # UPDATE

        if run_args.ha:
            logger.info("Configuring glusterfs")
            cmd = ['provisioner', 'setup', 'glusterfs']
            # TODO IMPROVE !!!
            #       that should be applied only for replace-node
            #       logic and no here
            if run_args.field_setup:
                cmd.append('--cleanup')
            if run_args.glusterfs_docker:
                cmd.append('--in-docker')
            if run_args.dist_type != config.DistrType.BUNDLE:
                cmd.append('--add-repo')
            cmd = ' '.join(utils.quote_shell_cmd(cmd))

            logger.debug(f"glusterfs config command: {cmd}")
            ssh_client.cmd_run(cmd, targets=run_args.primary.minion_id)

        #   CONFIGURE SALT
        logger.info("Configuring salt")
        ssh_client.cmd_run(
            'provisioner setup saltstack', targets=run_args.primary.minion_id
        )

        if not run_args.field_setup:
            # Note. in both cases (ha and non-ha) we need user pillar update
            # only on primary node, in case of ha it would be shared for other
            # masters
            # TODO retain service user password if already generated (on previous runs)
            logger.info("Preparing pillar")
            cmd = ['provisioner', 'setup', 'pillar']
            cmd.extend(['--release-type', run_args.dist_type.value])

            if run_args.url_cortx_deps:
                cmd.extend(['--release-deps-bundle-url', run_args.url_cortx_deps])

            if run_args.target_build:
                cmd.extend(['release-target-build', run_args.target_build])

            cmd = ' '.join(utils.quote_shell_cmd(cmd))
            ssh_client.cmd_run(cmd, targets=run_args.primary.minion_id)


        if run_args.target_build:
            # TODO IMPROVE non idempotent now
            logger.info("Get release factory version")
            if run_args.dist_type == config.DistrType.BUNDLE:
                url = f"{run_args.target_build}/cortx_iso"
            else:
                url = run_args.target_build

            if url.startswith(('http://', 'https://')):
                ssh_client.cmd_run(
                    (
                       f'curl {url}/RELEASE.INFO '
                       f'-o /etc/yum.repos.d/RELEASE_FACTORY.INFO'
                    )
                )
            elif url.startswith('file://'):
                # TODO TEST EOS-12076
                ssh_client.cmd_run(
                    (
                       f'cp -f {url[7:]}/RELEASE.INFO '
                       f'/etc/yum.repos.d/RELEASE_FACTORY.INFO'
                    )
                )
            else:
                raise ValueError(
                    f"Unexpected target build: {run_args.target_build}"
                )

        # TODO IMPROVE EOS-8473 FROM THAT POINT REMOTE SALT SYSTEM IS FULLY
        #      CONFIGURED AND MIGHT BE USED INSTEAD OF SALT-SSH BASED CONTROL

        logger.info("Sync salt modules")  # DONE
        res = ssh_client.cmd_run("salt-call saltutil.list_extmods")  # DONE
        logger.debug(f"Current list of extension modules: {res}")  # DONE
        res = ssh_client.cmd_run("salt-call saltutil.sync_modules")  # DONE
        logger.debug(f"Synced extension modules: {res}")  # DONE

        logger.info("Configuring provisioner logging")
        for state in [
            # 'components.system.prepare',
            'components.provisioner.config'
        ]:
            ssh_client.cmd_run(
                f"salt-call state.apply {state}",
                targets=master_targets
            )

        logger.info("Updating BMC IPs")
        ssh_client.cmd_run("salt-call state.apply components.misc_pkgs.ipmi")


    def run(self):
        # TODO update install repos logic (salt repo changes)
        # TODO firewall make more salt oriented
        # TODO sources: github | gitrepo | rpm
        # TODO get latest tags for github source

        # TODO IMPROVE EOS-8473 better configuration way
        salt_logger = logging.getLogger('salt.fileclient')
        salt_logger.setLevel(logging.WARNING)

        self.prepare()

        self.install()

        # Does not hang after adding glusterfs logic.
        logger.info("Configuring the firewall")  # UPDATE
        ssh_client.state_apply('firewall')  # UPDATE

        if not run_args.field_setup:
            logger.info("Copying factory data")
            ssh_client.state_apply(
                'provisioner.factory_profile',
                targets=run_args.primary.minion_id,
            )

        self.config()

        return self.setup_ctx


# TODO TEST EOS-8473
# TODO DOC highlights
#   - multiple setups support
#   - idempotence: might be run multiple times,
#       re-tries much faster (2-3 times)
#   - multi-salt-master initial support:
#       - list of salt-masters is auto-generated
#         (each to each reachability is checked)
#   - parallel setup of multiple nodes
#   - paswordless ssh setup to nodes is supported
@attr.s(auto_attribs=True)
class SetupProvisioner(SetupCmdBase, CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsSetupProvisionerGeneric

    def _run(self, nodes, **kwargs):  # noqa: C901 FIXME
        # validation
        # TODO IMPROVE EOS-8473 make generic logic
        run_args = RunArgsSetupProvisionerGeneric(nodes=nodes, **kwargs)
        runner = _Runner(run_args, profile)
        return runner.run()

    def run(self, *args, **kwargs):
        self._run(*args, **kwargs)

        logger.info("Done")
