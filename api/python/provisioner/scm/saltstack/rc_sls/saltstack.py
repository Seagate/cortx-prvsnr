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

import uuid
import logging
from typing import List, Optional, Dict
from pathlib import Path

from provisioner.vendor import attr
from provisioner import utils, config


from provisioner import errors

from provisioner.attr_gen import attr_ib
from provisioner.values import UNCHANGED, MISSED
from provisioner.resources import saltstack
# from provisioner.salt_minion import ensure_salt_minions_are_ready
from provisioner.pillar import PillarKey, PillarResolverNew
from provisioner.node import Node, NodeGrains

from .base import Resource3rdPartySLS

logger = logging.getLogger(__name__)


# SALT-STACK COMMON #

@attr.s
class SaltStackSLS(Resource3rdPartySLS):
    _base_sls = 'saltstack'

    def __attrs_post_init__(self):
        """No Ops."""


@attr.s
class SaltStackRepoSLS(SaltStackSLS):
    sls = 'repo'
    state_t = saltstack.SaltStackRepo


# SALT-MASTER #

@attr.s
class SaltMasterSLS(Resource3rdPartySLS):
    _base_sls = 'saltstack/salt-master'

    def __attrs_post_init__(self):
        """No Ops."""


@attr.s
class SaltMasterPrepareSLS(SaltMasterSLS):
    sls = 'prepare'
    state_t = saltstack.SaltMasterPrepare


@attr.s
class SaltMasterInstallSLS(SaltMasterSLS):
    sls = 'install'
    state_t = saltstack.SaltMasterInstall

    def setup_roots(self):
        super().setup_roots()
        pillar = {'lvm2_first': self.state.lvm2_first}
        self.pillar_set(pillar, expand=True)


@attr.s
class SaltMasterConfigSLS(SaltMasterSLS):
    sls = 'config'
    state_t = saltstack.SaltMasterConfig

    def setup_roots(self):
        super().setup_roots()

        self.pillar_inline['inline']['salt-master'] = {
            'onchanges': self.state.onchanges,
            'updated_keys': self.state.updated_keys
        }

    def _run(self):
        # TODO (outdated ?) IMPROVE EOS-9581 log salt-masters as well
        # TODO IMPROVE salt might be restarted in the background,
        #      might require to ensure that it is ready to avoid
        #      a race condition with further commands that relies
        #      on it (e.g. salt calls and provisioner api on a remote).
        #      To consider the similar logic as in salt_master.py.
        #
        #      Alternative: pospone that step once core and API
        #      is installed and we may call that on remotes
        try:
            super()._run()
        except errors.SaltCmdRunError as exc:
            if 'Stream is closed' in str(exc):
                logger.warning(
                    f"salt clien {type(self.client)} lost a stream, "
                    "trying a workaround"
                )
                for node in self.targets_list:
                    logger.info(f"stopping salt-master on {node}")
                    self.client.run(
                        'cmd.run', targets=node,
                        fun_args=['systemctl stop salt-master']
                    )

                logger.info(
                    "Starting salt-masters on all nodes. "
                    f"{self.targets_list}"
                )
                self.client.run(
                    'cmd.run', targets=self.targets_list,
                    fun_args=['systemctl start salt-master']
                )
            else:
                raise


@attr.s
class SaltMasterStartSLS(SaltMasterSLS):
    sls = 'start'
    state_t = saltstack.SaltMasterStart


@attr.s
class SaltMasterStopSLS(SaltMasterSLS):
    sls = None
    state_t = saltstack.SaltMasterStop

    def _run(self):
        try:
            logger.info("Stopping 'salt-master' service")
            self.client.state_single(
                "service.dead", targets=self.targets, fun_args=['salt-master']
            )
        except errors.SaltCmdRunError as exc:  # TODO DRY
            if 'Stream is closed' in str(exc):
                logger.warning(
                    "Ensuring salt-master was stopped "
                    "(salt-ssh lost a connection)"
                )
                self.client.run(
                    'cmd.run',
                    targets=self.targets,
                    fun_args=['systemctl stop salt-master']
                )


# SALT-MINION #

@attr.s
class SaltMinionSLS(Resource3rdPartySLS):
    _base_sls = 'saltstack/salt-minion'

    def __attrs_post_init__(self):
        """No Ops."""


@attr.s
class SaltMinionPrepareSLS(SaltMinionSLS):
    sls = 'prepare'
    state_t = saltstack.SaltMinionPrepare


@attr.s
class SaltMinionInstallSLS(SaltMinionSLS):
    sls = 'install'
    state_t = saltstack.SaltMinionInstall


@attr.s
class SaltMinionStartSLS(SaltMinionSLS):
    sls = 'start'
    state_t = saltstack.SaltMinionStart


@attr.s
class SaltMinionStopSLS(SaltMinionSLS):
    sls = None
    state_t = saltstack.SaltMinionStop

    def _run(self):
        logger.info("Stopping 'salt-minion' service")
        self.client.state_single(
            "service.dead", targets=self.targets, fun_args=['salt-mininon']
        )


@attr.s
class SaltMinionEnsureReadySLS(SaltMinionSLS):
    sls = None
    state_t = saltstack.SaltMinionEnsureReady

    def _run(self):
        raise NotImplementedError
        # ensure_salt_minions_are_ready(self.targets_list)


@attr.s
class SaltMinionConfigSLS(SaltMinionSLS):
    sls = 'config'
    state_t = saltstack.SaltMinionConfig

    master_nodes: Optional[Dict[str, Node]] = attr_ib(init=False, default=None)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

        if self.state.masters is not UNCHANGED:
            salt_ret = self.client.run(
                'grains.items',
                targets=self.state.masters,
            )
            node_grains = {
                node: NodeGrains.from_grains(
                    **salt_ret[node]
                ) for node in self.state.masters
            }

            self.master_nodes = {
                node: Node(node, grains.host, grains=grains)
                for node, grains in node_grains.items()
            }

            self._resolve_connections(
                [node for node in self.master_nodes.values()]
            )

    def _resolve_connections(self, nodes: List[Node]):
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

            targets = (
                [_node.minion_id for _node in nodes if _node is not node]
            )

            for addr in candidates:
                try:
                    self.client.cmd_run(
                        f"ping -c 1 -W 1 {addr}", targets=targets,
                    )
                except errors.SaltCmdResultError as exc:
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
                raise errors.ProvisionerError(
                    f"{node.minion_id} is not reachable"
                    f"from other nodes by any of {candidates}"
                )

            node.ping_addrs = list(pings)

    def setup_roots(self):
        super().setup_roots()

        self.pillar_inline['inline']['salt-minion'] = {
            'onchanges': self.state.onchanges
        }

        for node in self.targets_list:
            _pillar = self.pillar[node]

            node_uuid = _pillar.get('grains', {}).get('node_id')
            if not node_uuid:
                node_uuid = str(uuid.uuid4())

            # TODO IMPROVE EOS-8473 consider to move to mine data
            # (locally) prepare hostname info
            hostnamectl_status = _pillar.get(
                'grains', {}
            ).get('hostnamectl_status')

            if self.state.rediscover or not hostnamectl_status:
                res = self.client.cmd_run(
                    "hostnamectl status  | sed 's/^ *//g'",
                    fun_kwargs=dict(python_shell=True),
                    targets=node
                )
                # Note. output here is similar to yaml format
                # ensure that it is yaml parseable
                hostnamectl_status = utils.load_yaml_str(res[node])

            # prepare list of masters
            config_master = UNCHANGED
            roles = UNCHANGED
            if self.master_nodes:
                config_master = []
                for _node in self.targets_list:
                    # note: any node may be a salt-master
                    # TODO get rid of LOCALHOST_IP as
                    #      a special case for local master
                    if _node in self.master_nodes:
                        config_master.append(
                            config.LOCALHOST_IP if _node == node
                            # TODO review, might be not the best choice
                            else self.master_nodes[_node].ping_addrs[0]
                        )

                # FIXME hard-codes
                # FIXME not accurate in case of HA setup
                # TODO update only if needed
                roles = [
                    'primary' if (node in self.master_nodes) else 'secondary'
                ]

            # XXX write only on updates
            pillar = {
                'grains': {
                    'cluster_id': self.state.cluster_uuid,
                    'node_id': node_uuid,
                    'hostnamectl_status': hostnamectl_status,
                    'roles': roles
                },
                'config': {
                    'master': config_master
                }
            }
            self.pillar_set(pillar, targets=node, expand=True)


# SALT-CLUSTER #

@attr.s
class SaltClusterSLS(Resource3rdPartySLS):
    _base_sls = 'saltstack/salt-cluster'

    def __attrs_post_init__(self):
        """No Ops."""


@attr.s
class SaltClusterConfigSLS(SaltClusterSLS):
    sls = None
    state_t = saltstack.SaltClusterConfig

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

        # cluster UUID verification
        if self.state.cluster_uuid is UNCHANGED:
            if not self.cluster_uuid:
                self.state.cluster_uuid = str(uuid.uuid4())

        # masters list verification
        if self.state.masters is UNCHANGED:
            if not self.master_targets:
                self.state.masters = self.targets_list

        # covers two cases here:
        #   - new masters set is bad
        #   - old masters set is bad
        master_targets = (
            self.master_targets if self.state.masters is UNCHANGED
            else self.state.masters
        )
        diff = set(master_targets) - set(self.targets_list)
        if diff:
            raise ValueError(
                f'The following pillar masters are not expected: {diff}'
            )

    @property
    def cluster_uuid(self):
        pi_key = PillarKey('salt-minion/grains/cluster_id')
        pillar = PillarResolverNew(
            targets=self.targets, client=self.client
        ).get((pi_key,))

        ids = set([v[pi_key] for v in pillar.values()])

        if len(ids) != 1:
            # XXX more specific error here
            raise ValueError(f'unexpected cluster ids in pillar: {ids}')

        res = list(ids)[0]
        return (None if (not res or res is MISSED) else res)

    @property
    def master_targets(self):
        # Note. assumption: masters are the same for all targets
        res = next(iter(self.pillar.values())).get('masters')
        return ([] if (not res or res is MISSED) else res)

    def preseed_keys(self):
        salt_master_pki_dir = self.fileroot_path("pki/master")

        # TODO IMPROVE review, check the alternatives as more secure ways
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster_pki.html  # noqa: E501
        #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html  # noqa: E501
        master_key_pem = salt_master_pki_dir / 'master.pem'
        master_key_pub = salt_master_pki_dir / 'master.pub'
        if self.state.regen_keys or not (
            master_key_pem.exists() and master_key_pub.exists()
        ):
            # FIXME violates FileRoot encapsulation, better way:
            # - generate in some temp location
            # - copy to fileroot
            salt_master_pki_dir.mkdir(parents=True, exist_ok=True)
            utils.run_subprocess_cmd(
                [
                    'salt-key',
                    '--gen-keys', master_key_pem.stem,
                    '--gen-keys-dir', str(salt_master_pki_dir)
                ]
            )

        for node in self.targets_list:
            node_pki_dir = self.fileroot_path(f"pki/minions/{node}")

            #   preseed minion keys
            node_key_pem_tmp = node_pki_dir / f'{node}.pem'
            node_key_pub_tmp = node_pki_dir / f'{node}.pub'
            node_key_pem = node_pki_dir / 'minion.pem'
            node_key_pub = node_pki_dir / 'minion.pub'

            node_key_pub_for_master_r_path = Path("pki/master/minions") / node

            # XXX that avoids unnecessary generation of keys but would
            #     fail if the keys are not in sync between each other
            if self.state.regen_keys or not (
                node_key_pem.exists()
                and node_key_pub.exists()
                and self.fileroot_path(node_key_pub_for_master_r_path)
            ):
                node_pki_dir.mkdir(parents=True, exist_ok=True)
                utils.run_subprocess_cmd(
                    [
                        'salt-key',
                        '--gen-keys', node,
                        '--gen-keys-dir', str(node_pki_dir)
                    ]
                )
                node_key_pem_tmp.rename(node_key_pem)
                node_key_pub_tmp.rename(node_key_pub)

                self.fileroot_copy(
                    node_key_pub, node_key_pub_for_master_r_path
                )

    def setup_roots(self):
        super().setup_roots()
        self.pillar_set({'masters': self.state.masters}, expand=True)
        self.preseed_keys()

    def _run(self):
        logger.info("Configuring salt minions")
        res = SaltMinionConfigSLS(
            state=saltstack.SaltMinionConfig(
                masters=self.state.masters,
                cluster_uuid=self.state.cluster_uuid,
                onchanges=self.state.onchanges_minion,
                rediscover=self.state.rediscover
            ),
            client=self.client,
            targets=self.targets
        ).run()[0]  # minion runs only one sls

        # resolving minions which keys have been updated
        updated_keys = []
        # TODO IMPROVE EOS-8473
        minion_pki_state_id = 'file_|-salt_minion_pki_set_|-/etc/salt/pki/minion_|-recurse'  # noqa: E501
        for node_id, _res in res.items():
            if _res[minion_pki_state_id]['changes']:
                updated_keys.append(node_id)
        logger.debug(f'Updated salt minion keys: {updated_keys}')

        logger.info("Configuring salt masters")
        res = SaltMasterConfigSLS(
            state=saltstack.SaltMasterConfig(
                onchanges=self.state.onchanges_master,
                updated_keys=updated_keys
            ),
            client=self.client,
            targets=(
                self.master_targets if self.state.masters is UNCHANGED
                else self.state.masters
            )
        ).run()
