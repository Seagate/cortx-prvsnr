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


# import logging
#
# from provisioner.vendor import attr
#
# logger = logging.getLogger(__name__)
#
#
# @attr.s(auto_attribs=True)
# class SaltMaster(Resource):
#     name = 'salt-master'
#
#
# class SaltMasterSLS(ResourceSLS):
#     resource = SaltMaster
#
#
# @attr.s(auto_attribs=True)
# class Install(SaltMasterSLS):
#     name = 'install'
#     state_name = 'saltstack.salt_master.install'
#
#
# @attr.s(auto_attribs=True)
# class Stop(SaltMasterSLS):
#     name = 'stop'
#     state_name = 'saltstack.salt_master.install'
#
#     def run(self):
#         try:
#             logger.info(f"Stopping 'salt-master' service")
#             self.client.state_single(
#                 "service.dead", fun_args=['salt-master']
#             )
#         except SaltCmdRunError as exc:  # TODO DRY
#             if 'Stream is closed' in str(exc):
#                 logger.warning(
#                     "Ensuring salt-master was stopped "
#                     "(salt-ssh lost a connection)"
#                 )
#                 self.client.run(
#                     'cmd.run', fun_args=['systemctl stop salt-master']
#                 )
#
#
# @attr.s(auto_attribs=True)
# class Config(SaltMasterSLS):
#     name = 'config'
#     state_name = 'saltstack.salt_master.config'
#
#
# @attr.s(auto_attribs=True)
# class SaltMasterStart(ResourceSLS):
#     resource = 'salt-master'
#     state_name = 'saltstack.salt-master.start'
#
#
# @attr.s(auto_attribs=True)
# class SaltMinion(Resource):
#     name = 'salt-minion'
#
#
# class SaltMinionSLS(ResourceSLS):
#     resource = SaltMinion
#
#
# @attr.s(auto_attribs=True)
# class Install(SaltMinionSLS):
#     name = 'install'
#     state_name = 'saltstack.salt_minion.install'
#
#
# @attr.s(auto_attribs=True)
# class Stop(SaltMinionSLS):
#     name = 'stop'
#
#     # XXX move to SLS
#     def run(self):
#         logger.info(f"Stopping 'salt-minion' service")
#         self.client.state_single(
#             "service.dead", fun_args=['salt-mininon']
#         )
#
#
# @attr.s(auto_attribs=True)
# class SaltMinionConfig(SaltMinionSLS):
#     name = 'config'
#     state_name = 'saltstack.salt_minion.config'
#
#     rediscover: bool = RunArgsSetup.rediscover
#     nodes: List
#
#     def setup_roots(self, targets):
#         pillar_setup = salt_client.pillar_get(
#             'setup/saltstack/salt_minion', targets
#         )
#
#         for node in self.nodes:
#             _pillar = pillar_setup[node.minion_id]
#
#             node_uuid = _pillar['grains']['node_id']
#             if not node_uuid:
#                 node_uuid = str(uuid.uuid4())
#
#             # TODO IMPROVE EOS-8473 consider to move to mine data
#             # (locally) prepare hostname info
#             hostnamectl_status = _pillar['grains']['hostnamectl_status']
#             if self.rediscover or not hostnamectl_status:
#                 res = self.client.cmd_run(
#                     "hostnamectl status  | sed 's/^ *//g'",
#                     fun_kwargs=dict(python_shell=True),
#                     targets=node.minion_id
#                 )
#                 # Note. output here is similar to yaml format
#                 # ensure that it is yaml parseable
#                 hostnamectl_status = load_yaml_str(res[node.minion_id])
#
#             pi_key_base = PillarKey('setup/saltstack/salt_minion')
#
#             # XXX write only on updates
#             salt_client.pillar_set([
#                 (pi_key_base / 'grains/node_id', node_uuid)
#                 (pi_key_base / 'grains/hostnamectl_status', hostnamectl_status)
#             ])
#
#
# @attr.s(auto_attribs=True)
# class SaltMinionStart(ResourceSLS):
#     resource = 'salt-minion'
#     state_name = 'saltstack.salt-minion.start'
#
#
# @attr.s(auto_attribs=True)
# class SaltMinionEnsureReady(ResourceSLS):
#     resource = 'salt-minion'
#     state_name = None
#
#     def run(self):
#         ensure_salt_minions_are_ready(self.client.targets_list())
#
#
# @attr.s(auto_attribs=True)
# class SaltCluster(Resource):
#     name = 'saltstack.cluster'
#
#
# class SaltClusterSLS(ResourceSLS):
#     resource = SaltCluster
#
#
# @attr.s(auto_attribs=True)
# class Config(SaltClusterSLS):
#     name = 'config'
#     state_name = None
#
#     nodes: List[Node]
#
#     cluster_uuid: Union[str, _PrvsnrValue] = attr_ib(default=UNCHANGED)
#     masters: Union[List[Node], _PrvsnrValue] = attr_ib(default=UNCHANGED)
#
#     def __attrs_post_init__(self):
#
#         # prepare cluster UUID
#         if self.cluster_uuid is UNCHANGED:
#             pillar_setup = salt_client.pillar_get(
#                 'setup/saltstack/salt_minion', targets
#             )
#
#             _pillar = pillar_setup[node.minion_id]
#             ids = set()
#             for node in nodes:
#                 _pillar = pillar_setup[node.minion_id]
#                 ids.add(_pillar.get('grains', {}).get('cluster_id'))
#
#             if len(ids) != 1:
#                 # XXX more specific error here
#                 raise ValueError(f'unexpected cluster ids in pillar: {ids}')
#
#             self.cluster_uuid = list(ids)[0]
#
#         if self.masters is UNCHANGED:
#             pillar_masters = salt_client.pillar_get(
#                 'saltstack/masters', local_minion_id
#             )
#
#             _masters = []
#             for node in self.nodes:
#                 if node.minion_id in pillar_masters:
#                     _masters.append(node)
#
#             diff = set(pillar_masters) - set([n.minion_id for n in _masters])
#             if diff:
#                 raise ValueError(
#                     f'The following pillar masters are not expected: {diff}'
#                 )
#
#             self.masters = _masters
#
#         else:
#             diff = set(self.masters) - set(self.nodes)
#             if diff:
#                 raise ValueError(
#                     f'The following masters are not expected: {diff}'
#                 )
#
#     def preseed_keys(self, targets):
#         salt_master_pki_dir = self.fileroot_path("master/pki")
#         salt_master_minions_pki_dir = salt_master_pki_dir / "minions"
#
#         # TODO IMPROVE review, check the alternatives as more secure ways
#         #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster_pki.html  # noqa: E501
#         #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html  # noqa: E501
#         master_key_pem = salt_master_pki_dir / 'master.pem'
#         master_key_pub = salt_master_pki_dir / 'master.pub'
#         if not (
#             master_key_pem.exists()
#             and master_key_pub.exists()
#         ):
#             # FIXME violates FileRoot encapsulation, better way:
#             # - generate in some temp location
#             # - copy to fileroot
#             run_subprocess_cmd(
#                 [
#                     'salt-key',
#                     '--gen-keys', master_key_pem.stem,
#                     '--gen-keys-dir', str(salt_master_pki_dir)
#                 ]
#             )
#
#         for node in run_args.nodes:
#             node_dir = self.fileroot_path(f"minions/{node.minion_id}")
#             node_pki_dir = node_dir / 'pki'
#             node_pki_dir.mkdir(parents=True, exist_ok=True)
#
#             #   preseed minion keys
#             node_key_pem_tmp = node_pki_dir / f'{node.minion_id}.pem'
#             node_key_pub_tmp = node_pki_dir / f'{node.minion_id}.pub'
#             node_key_pem = node_pki_dir / 'minion.pem'
#             node_key_pub = node_pki_dir / 'minion.pub'
#
#             if not (node_key_pem.exists() and node_key_pub.exists()):
#                 run_subprocess_cmd(
#                     [
#                         'salt-key',
#                         '--gen-keys', node.minion_id,
#                         '--gen-keys-dir', str(node_pki_dir)
#                     ]
#                 )
#                 node_key_pem_tmp.rename(node_key_pem)
#                 node_key_pub_tmp.rename(node_key_pub)
#
#             run_subprocess_cmd(
#                 [
#                     'cp', '-f',
#                     str(node_key_pub),
#                     str(salt_master_minions_pki_dir / node.minion_id)
#                 ]
#             )
#
#             fileroot.refresh()
#
#     def setup_salt_minions_roots(self):
#         SaltMinionConfig().setup_roots()
#
#         pillar_setup = salt_client.pillar_get(
#             'setup/saltstack/salt_minion', targets
#         )
#         for node in self.nodes:
#             _pillar = pillar_setup[node.minion_id]
#
#             if self.cluster_uuid is None:
#                 cluster_uuid = str(uuid.uuid4())
#
#             # prepare list of masters
#             masters = []
#             for _node in self.nodes:
#                 # note: any node may be a salt-master
#                 if _node in self.masters:  # XXX
#                     masters.append(
#                         config.LOCALHOST_IP if _node is node
#                         else _node.ping_addrs[0]
#                     )
#
#             # XXX hard-codes
#             # FIXME not accurate in case of HA setup
#             roles = ['primary' if (node in self.masters) else 'secondary']
#
#             pi_key_base = PillarKey('setup/saltstack/salt_minion')
#
#             # XXX write only on updates
#             salt_client.pillar_set([
#                 (pi_key_base / 'config/master', masters),
#                 (pi_key_base / 'grains/roles', roles),
#                 (pi_key_base / 'grains/cluster_id', cluster_uuid)
#             ])
#
#     def setup_salt_masters_roots(self):
#         SaltMasterConfig().setup_roots()
#
#     def setup_salt_cluster_roots(self):
#         self.preseed_keys()
#
#     def setup_roots(self):
#         self.setup_salt_cluster_roots()
#         self.setup_salt_minions_roots()
#         self.setup_salt_masters_roots()
#
#     def run(self, targets):
#
#         logger.info("Configuring salt minions")
#         res = self.client.state_apply(
#             'saltstack.cluster.config_salt_minion',
#             fun_kwargs={
#                 'pillar': {
#                     'inline': {
#                         'saltstack': {
#                             'salt_minion': {
#                                 # XXX hard-coded
#                                 'onchanges': 'stop'
#                             }
#                         }
#                     }
#                 }
#             }
#         )
#
#         updated_keys = []
#         # TODO IMPROVE EOS-8473
#         minion_pki_state_id = 'file_|-salt_minion_pki_set_|-/etc/salt/pki/minion_|-recurse'  # noqa: E501
#         for node_id, _res in res.items():
#             if _res[minion_pki_state_id]['changes']:
#                 updated_keys.append(node_id)
#         logger.debug(f'Updated salt minion keys: {updated_keys}')
#
#         # TODO DOC how to pass inline pillar
#         # TODO IMPROVE EOS-9581 log salt-masters as well
#         # TODO IMPROVE salt might be restarted in the background,
#         #      might require to ensure that it is ready to avoid
#         #      a race condition with further commands that relies
#         #      on it (e.g. salt calls and provisioner api on a remote).
#         #      To consider the similar logic as in salt_master.py.
#         #
#         #      Alternative: pospone that step once core and API
#         #      is installed and we may call that on remotes
#         try:
#             self.client.state_apply(
#                 'saltstack.cluster.config_salt_master',
#                 targets=master_targets,
#                 fun_kwargs={
#                     'pillar': {
#                         'inline': {
#                             'saltstack': {
#                                 'salt_master': {
#                                     'updated_keys': updated_keys,
#                                     # XXX hard-coded
#                                     'onchanges': 'restart'
#                                 }
#                             }
#                         }
#                     }
#                 }
#             )
#         except SaltCmdRunError as exc:
#             if 'Stream is closed' in str(exc):
#                 logger.warning('salt-ssh lost a stream, trying to workaround')
#                 # FIXME dirty code
#                 targets = (
#                     [node.minion_id for node in run_args.nodes]
#                     if master_targets == ALL_MINIONS else [master_targets]
#                 )
#
#                 for target in targets:
#                     logger.info(f"stopping salt-master on {target}")
#                     self.client.run(
#                         'cmd.run', targets=target,
#                         fun_args=['systemctl stop salt-master']
#                     )
#
#                 logger.info(
#                     "Starting salt-masters on all nodes. "
#                     f"{master_targets}"
#                 )
#                 self.client.run(
#                     'cmd.run', targets=master_targets,
#                     fun_args=['systemctl start salt-master']
#                 )
#             else:
#                 raise
#
#
# @attr.s(auto_attribs=True)
# class SaltMinionConfig(ResourceSLS):
#     resource = 'salt-minion'
#     state_name = 'components...salt-minion.config'
#     masters
#     grains
#     master key
#     minion key
#
#     # assumptions:
#     #   - provisioner core is installed, templates:
#     #       - minion config
#     #       - minion grains
#     #   - minion pki is in fileroot
#     #   - master pub is in fileroot
#     #   - master IPs are in pillar
#
# # assumptions:
# # - salt-ssh env is configured:
# #   - roster file is up to date
# #   - /etc/salt/master is set
# #   - pillar for connections are set
# @attr.s(auto_attribs=True)
# class SaltStack(ComponentBase):
#     name = 'saltstack'
#
#     ha: bool = attr_ib(cli_spec='setup/ha', default=False)
#     masters: List[NodeExt] = attr.ib(init=False, default=None)
#     minions: List[NodeExt] = attr.ib(init=False, default=None)
#
#     _self.client: SaltSSHClient = attr.ib(init=False, default=None)
#     _targets: List = attr.ib(init=False, default=None)
#     _nodes: List[NodeExt] = attr.ib(init=False, default=None)
#     _master_targets: str = attr.ib(init=False, default=None)
#
#     @property
#     def primary(self):
#         return self._nodes[0]
#
#     @property
#     def secondaries(self):
#         return self._nodes[1:]
#
#     def __attrs_post_init__(self):
#         self._targets = self._self.client.roster_targets()
#         self._self.client = SaltSSHClient()
#
#         self._nodes = [
#             NodeExt(_id, _data['host'], _data['user'], _data['port'])
#             for _id, _data in self._self.client.roster_data().items()
#         ]
#
#         self._master_targets = (
#             ALL_MINIONS if self.ha else self._targets[0]
#         )
#
#         # resolving connections info
#         self._set_salt_masters()
#
#     def _set_salt_masters(self):
#         res = {}
#
#         if not self._nodes:
#             raise ProvisionerRuntimeError('no nodes defined found')
#
#         if len(self._nodes) == 1:
#             res[self._nodes[0].minion_id] = [
#                 self.salt_master if self.salt_master
#                 else config.LOCALHOST_IP
#             ]
#         elif self.salt_master:
#             res = {
#                 node.minion_id: [self.salt_master]
#                 for node in self._nodes
#             }
#         else:
#             # FIXME
#             Connections().resolve(self._nodes)
#
#             # NOTE change of the logic
#             master_nodes = (
#                 self._nodes if self.ha else [self.primary]
#             )
#             res = {
#                 node.minion_id: node.conns[ConnT.SALTSTACK]
#                 for node in master_nodes
#                 if node.conns[ConnT.SALTSTACK]
#             }
#
#         if not res:
#             raise ProvisionerRuntimeError(
#                 'no SaltStack master connections found'
#             )
#
#         for node in self._nodes:
#             node.masters = salt_masters
#
#     # TODO IMPROVE many hard coded values
#     def _set_salt_pki(self, run_args, self.client, paths):  # noqa: E501, C901 FIXME
#         fileroot = FileRoot(USER_SHARED_FILEPATH, refresh_on_update=False)
#
#         minions_dir = "components/provisioner/setup/files/minions"
#         all_minions_dir = minions_dir / 'all'
#         salt_master_pki_dir = "components/provisioner/setup/salt_master/files/pki"
#         salt_master_minions_pki_dir = salt_master_pki_dir / 'minions'
#
#         cluster_id_path = all_minions_dir / 'cluster_id'
#         if not fileroot.exists(cluster_id_path):
#             cluster_uuid = str(uuid.uuid4())
#             fileroot.write_yaml(cluster_id_path, dict(cluster_id=cluster_uuid))
#         else:
#             cluster_uuid = fileroot.read_yaml(cluster_id_path)['cluster_id']
#
#         # TODO IMPROVE review, check the alternatives as more secure ways
#         #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster_pki.html  # noqa: E501
#         #    - https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html  # noqa: E501
#         master_key_pem = salt_master_pki_dir / 'master.pem'
#         master_key_pub = salt_master_pki_dir / 'master.pub'
#         if not (
#             fileroot.exists(master_key_pem)
#             and fileroot.exists(master_key_pub)
#         ):
#             master_key_pem = fileroot.path(master_key_pem)
#             master_key_pub = fileroot.path(master_key_pub)
#
#             # FIXME violates FileRoot encapsulation
#             run_subprocess_cmd(
#                 [
#                     'salt-key',
#                     '--gen-keys', master_key_pem.stem,
#                     '--gen-keys-dir', str(salt_master_pki_dir)
#                 ]
#             )
#
#         for node in run_args.nodes:
#             node_dir = minions_dir / f"{node.minion_id}"
#             node_pki_dir = node_dir / 'pki'
#             node_pillar_dir = pillar_minions_dir / f"{node.minion_id}"
#
#             #   ensure parent dirs exists in profile file root
#             node_pki_dir.mkdir(parents=True, exist_ok=True)
#             node_pillar_dir.mkdir(parents=True, exist_ok=True)
#
#             #   TODO IMPROVE use salt caller and file-managed instead
#             #   (locally) prepare minion node_id
#             minion_nodeid_path = node_dir / 'node_id'
#             if not minion_nodeid_path.exists():
#                 node_uuid = str(uuid.uuid4())
#                 dump_yaml(minion_nodeid_path, dict(node_id=node_uuid))
#             else:
#                 node_uuid = load_yaml(minion_nodeid_path)['node_id']
#
#             # TODO IMPROVE EOS-8473 consider to move to mine data
#             # (locally) prepare hostname info
#             minion_hostname_status_path = node_dir / 'hostname_status'
#             if run_args.rediscover or not minion_hostname_status_path.exists():
#                 res = self.client.cmd_run(
#                     "hostnamectl status  | sed 's/^ *//g'",
#                     fun_kwargs=dict(python_shell=True),
#                     targets=node.minion_id
#                 )
#                 # Note. output here is similar to yaml format
#                 # ensure that it is yaml parseable
#                 hostnamectl_status = load_yaml_str(res[node.minion_id])
#                 dump_yaml(
#                     minion_hostname_status_path,
#                     dict(hostname_status=hostnamectl_status)
#                 )
#             else:
#                 hostnamectl_status = load_yaml(
#                     minion_hostname_status_path
#                 )['hostname_status']
#
#             setup_pillar_path = add_pillar_merge_prefix(
#                 node_pillar_dir / 'setup.sls'
#             )
#             if run_args.rediscover or not setup_pillar_path.exists():
#                 data = {
#                     'setup': {
#                         'config': {
#                             'master': masters[node.minion_id]
#                         },
#                         'grains': [
#                             # FIXME not accurate in case of HA setup
#                             {'roles': [
#                                 'primary' if (node is run_args.primary)
#                                 else 'secondary'
#                             ]},
#                             {'cluster_id': cluster_uuid},
#                             {'node_id': node_uuid},
#                             {'hostname_status': hostnamectl_status},
#                         ]
#                     }
#                 }
#                 dump_yaml(setup_pillar_path, data)
#
#             #   preseed minion keys
#             node_key_pem_tmp = node_pki_dir / f'{node.minion_id}.pem'
#             node_key_pub_tmp = node_pki_dir / f'{node.minion_id}.pub'
#             node_key_pem = node_pki_dir / 'minion.pem'
#             node_key_pub = node_pki_dir / 'minion.pub'
#
#             if not (node_key_pem.exists() and node_key_pub.exists()):
#                 run_subprocess_cmd(
#                     [
#                         'salt-key',
#                         '--gen-keys', node.minion_id,
#                         '--gen-keys-dir', str(node_pki_dir)
#                     ]
#                 )
#                 node_key_pem_tmp.rename(node_key_pem)
#                 node_key_pub_tmp.rename(node_key_pub)
#
#             run_subprocess_cmd(
#                 [
#                     'cp', '-f',
#                     str(node_key_pub),
#                     str(salt_master_minions_pki_dir / node.minion_id)
#                 ]
#             )
#
#
#             fileroot.refresh()
#
#
# @attr.s(auto_attribs=True)
# class SaltStackManager(ClusteredServiceManagerBase):
#     name = 'SaltStackManager'
#
#     comp: SaltStack
#
#     _self.client: SaltSSHClient = attr.ib(init=False, default=None)
#     _targets: List = attr.ib(init=False, default=None)
#     _nodes: List[NodeExt] = attr.ib(init=False, default=None)
#     _master_targets: str = attr.ib(init=False, default=None)
#
#     def __attrs_post_init__(self):
#         self._targets = self._self.client.roster_targets()
#         self._self.client = SaltSSHClient()
#
#         self._nodes = [
#             NodeExt(_id, _data['host'], _data['user'], _data['port'])
#             for _id, _data in self._self.client.roster_data().items()
#         ]
#
#         self._master_targets = (
#             ALL_MINIONS if self.comp.ha else self._targets[0]
#         )
#
#         if not self.comp.masters:
#             # resolving connections info
#             self._set_salt_masters()
#
#         if not self.comp.minions:
#             self.comp.minions = self._nodes
#
#     @abstractmethod
#     def config(self, comp: Any, targets=ALL_MINIONS):
#         # TODO set setup:cofig:master basing on setup:connections
#         #      (or cluster...pvt_ip_addr if no data)
#
#         logger.info("Configuring salt minions")
#         res = self.client.state_apply(
#             'components.provisioner.setup.salt_minion',
#             targets=ALL_MINIONS)
#
#         updated_keys = []
#         # TODO IMPROVE EOS-8473
#         minion_pki_state_id = 'file_|-salt_minion_pki_set_|-/etc/salt/pki/minion_|-recurse'  # noqa: E501
#         for node_id, _res in res.items():
#             if _res[minion_pki_state_id]['changes']:
#                 updated_keys.append(node_id)
#         logger.debug(f'Updated salt minion keys: {updated_keys}')
#
#         # TODO DOC how to pass inline pillar
#
#         # TODO IMPROVE EOS-9581 log salt-masters as well
#         # TODO IMPROVE salt might be restarted in the background,
#         #      might require to ensure that it is ready to avoid
#         #      a race condition with further commands that relies
#         #      on it (e.g. salt calls and provisioner api on a remote).
#         #      To consider the similar logic as in salt_master.py.
#         #
#         #      Alternative: pospone that step once core and API
#         #      is installed and we may call that on remotes
#         try:
#             logger.info("Configuring salt-masters")
#             self.client.state_apply(
#                 'components.provisioner.setup.salt_master',
#                 targets=self._master_targets,
#                 fun_kwargs={
#                     'pillar': {
#                         'updated_keys': updated_keys
#                     }
#                 }
#             )
#         except SaltCmdRunError as exc:
#             if 'Stream is closed' in str(exc):
#                 logger.warning('salt-ssh lost a stream, trying to workaround')
#                 # FIXME dirty code
#                 targets = (
#                     self.self.client.roster_targets()
#                     if self._master_targets == ALL_MINIONS
#                     else [self._master_targets]
#                 )
#
#                 for target in targets:
#                     logger.info(f"stopping salt-master on {target}")
#                     self.client.run(
#                         'cmd.run', targets=target,
#                         fun_args=['systemctl stop salt-master']
#                     )
#
#                 logger.info(f"Starting salt-masters on {self._master_targets}")
#                 self.client.run(
#                     'cmd.run', targets=self._master_targets,
#                     fun_args=['systemctl start salt-master']
#                 )
#             else:
#                 raise
#
#     def start(self, comp: Any, targets=ALL_MINIONS):
#         logger.info("Starting salt minions")
#         self.client.state_apply('components.provisioner.salt_minion.start')
#
#         # TODO EOS-14019 might consider to move to right after restart
#         logger.info("Ensuring salt-masters are ready")
#         self.client.state_apply(
#             'components.provisioner.salt_master.start',
#             targets=self._master_targets
#         )
#
#         # TODO IMPROVE EOS-8473
#         # Note. we run the same on all masters to verify each master
#         #       connection to minions
#         logger.info("Ensuring salt minions are ready")
#         nodes_ids = [node.minion_id for node in run_args.nodes]
#         self.client.cmd_run(
#             (
#                 f"python3 -c \"from provisioner import salt_minion; "
#                 f"salt_minion.ensure_salt_minions_are_ready({nodes_ids})\""
#             ),
#             targets=self._master_targets
#         )
#
#
#     def stop(self, comp: Any, targets=ALL_MINIONS):
#         raise NotImplementedError
#
#     def teardown(self, comp: Any, targets=ALL_MINIONS):
#         raise NotImplementedError
#
