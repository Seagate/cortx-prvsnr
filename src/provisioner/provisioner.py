# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import errno
import os
from cortx.utils.process import SimpleProcess
from cortx.utils.conf_store import Conf
from cortx.utils.security.cipher import Cipher
from cortx.provisioner import const
from cortx.provisioner.log import CortxProvisionerLog, Log
from cortx.provisioner.error import CortxProvisionerError
from cortx.provisioner.config_store import ConfigStore
from cortx.utils.conf_store.error import ConfError
from cortx.provisioner.config import CortxConfig
from cortx.provisioner.cluster import CortxCluster,  CortxStorageSet
from cortx.provisioner.release import CortxRelease


class CortxProvisioner:
    """ CORTX Provosioner """

    _config_store_url = "yaml:///etc/cortx/cluster.conf"
    _solution_index = "solution_conf"
    _secrets_path = "/etc/cortx/solution/secret"

    @staticmethod
    def init():
        pass

    @staticmethod
    def config_apply(solution_config_url: str, config_store_url: str = None,
        force_override: bool = False):
        """
        Description:
        Parses input config and store in CORTX config location
        Parameters:
        [IN]  Solution Config URL
        [OUT] CORTX Config URL
        """
        if Log.logger is None:
            CortxProvisionerLog.initialize(const.SERVICE_NAME, const.TMP_LOG_PATH)

        if config_store_url is None:
            config_store_url = CortxProvisioner._config_store_url
        config_store = ConfigStore(config_store_url)

        # Check if config is already applied.
        if config_store.get('cortx>common>release') and force_override is False:
            Log.info('CORTX config already applied on this node.')
            return 0

        cortx_release = CortxRelease()
        # Load same config again if force_override is True
        # To load same config pass fail_reload=False.
        try:
            fail_reload = False if force_override else True
            Log.info('Applying config %s' % solution_config_url)
            Conf.load(CortxProvisioner._solution_index, solution_config_url,
                fail_reload=fail_reload)
        except ConfError as e:
            Log.error(f'Unable to load {solution_config_url} url, Error:{e}')

        # source code for encrypting and storing secret key
        if Conf.get(CortxProvisioner._solution_index, 'cluster') is not None:
            CortxProvisioner.solution_cluster_apply(config_store, cortx_release)

        if Conf.get(CortxProvisioner._solution_index, 'cortx') is not None:
            # generating cipher key
            cipher_key = None
            cluster_id = Conf.get(CortxProvisioner._solution_index, 'cluster>id')
            if cluster_id is None:
                cluster_id = config_store.get('cluster>id')
                if cluster_id is None:
                    raise CortxProvisionerError(errno.EINVAL, 'Cluster ID not specified')
            cipher_key = Cipher.gen_key(cluster_id, 'cortx')
            if cipher_key is None:
                raise CortxProvisionerError(errno.EINVAL, 'Cipher key not specified')
            for key in Conf.get_keys(CortxProvisioner._solution_index):
                # using path /etc/cortx/solution/secret to confirm secret
                if key.endswith('secret'):
                    secret_val = Conf.get(CortxProvisioner._solution_index, key)
                    val = None
                    with open(os.path.join(CortxProvisioner._secrets_path, secret_val), 'rb') as secret:
                        val = secret.read()
                    if val is None:
                        raise CortxProvisionerError(errno.EINVAL,
                            f'Could not find the Secret in  {CortxProvisioner._secrets_path}')
                    val = Cipher.encrypt(cipher_key, val)
                    # decoding the byte string in val variable
                    Conf.set(CortxProvisioner._solution_index, key, val.decode('utf-8'))
            CortxProvisioner.solution_config_apply(config_store, cortx_release)

    @staticmethod
    def solution_config_apply(config_store, cortx_release):
        """ Convert CORTX config into confstore keys """
        config_info = Conf.get(CortxProvisioner._solution_index, 'cortx')
        cortx_config = CortxConfig(config_info, cortx_release)
        cortx_config.save(config_store)

    @staticmethod
    def solution_cluster_apply(config_store, cortx_release):
        node_map = {}
        try:
            node_types = Conf.get(CortxProvisioner._solution_index, 'cluster>node_types')
            cluster_id = Conf.get(CortxProvisioner._solution_index, 'cluster>id')
            cluster_name = Conf.get(CortxProvisioner._solution_index, 'cluster>name')
            storage_sets = Conf.get(CortxProvisioner._solution_index, 'cluster>storage_sets')
            for key in [cluster_id, cluster_name, storage_sets, node_types]:
                if key is None:
                    raise CortxProvisionerError(
                        errno.EINVAL,
                        f"One of the key [id, name,storage_sets,node_types]"
                        " is unspecified for cluster.")

            for node_type in node_types:
                node_map[node_type['name']] = node_type

            cluster_keys = [('cluster>id', cluster_id),
                ('cluster>name', cluster_name),
                ('cluster>storage_set_count', len(storage_sets))]
            config_store.set_kvs(cluster_keys)

            nodes = []
            for storage_set in storage_sets:
                for node in storage_set['nodes']:
                    node_type = node['type']
                    node = dict(node_map[node_type], **node)
                    if node['type'] == 'storage_node':
                        cvg_list = node.pop('storage')
                        for cvg in cvg_list:
                            metadata_device = cvg['devices']['metadata']
                            # Convert metadata value to list.
                            if isinstance(metadata_device, str):
                                cvg['devices']['metadata'] = metadata_device.split(',')
                        node['storage'] = {
                            'cvg_count': len(cvg_list),
                            'cvg': cvg_list
                        }
                    node['storage_set'] = storage_set['name']
                    node['cluster_id'] = cluster_id
                    nodes.append(node)

            cluster_nodes = CortxCluster(nodes, cortx_release)
            cluster_nodes.save(config_store)
            cluster_storagesets = CortxStorageSet(storage_sets)
            cluster_storagesets.save(config_store)
        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while applying cluster_config {e}')

    @staticmethod
    def cluster_bootstrap(config_store_url: str = None, force_override: bool = False):
        """
        Description:
        Configures Cluster Components
        1. Reads Cortx Config and obtain cluster components
        2. Invoke Mini Provisioners of cluster components
        Paramaters:
        [IN] CORTX Config URL
        """

        if config_store_url is None:
            config_store_url = CortxProvisioner._config_store_url
        config_store = ConfigStore(config_store_url)

        node_id = Conf.machine_id
        if node_id is None:
            raise CortxProvisionerError(errno.EINVAL, 'Invalid node_id: %s', \
                node_id)

        # Reinitialize logging with configured log path
        log_path = os.path.join(
            config_store.get('cortx>common>storage>log'), const.APP_NAME, node_id)
        log_level = os.getenv('CORTX_PROVISIONER_DEBUG_LEVEL', const.DEFAULT_LOG_LEVEL)
        CortxProvisionerLog.reinitialize(
            const.SERVICE_NAME, log_path, level=log_level)

        phase = config_store.get(f'node>{node_id}>provisioning>phase')
        status = config_store.get(f'node>{node_id}>provisioning>status')
        if phase == "deployment" and status == "success" and force_override is False:
            Log.info('CORTX is already configured on this node.')
            return 0

        if config_store.get(f'node>{node_id}') is None:
            raise CortxProvisionerError(
                errno.EINVAL, f"Node id '{node_id}' not found in cortx config.")

        node_name = config_store.get(f'node>{node_id}>name')

        Log.info(f'Starting cluster bootstrap on {node_id}:{node_name}')

        CortxProvisioner._update_provisioning_info(
            config_store, node_id, 'deployment')
        components = config_store.get(f'node>{node_id}>components')
        if components is None:
            Log.warn(f"No component specified for {node_name} in CORTX config")
        num_components = len(components)
        mp_interfaces = ['post_install', 'prepare', 'config', 'init']
        for interface in mp_interfaces:
            for comp_idx in range(0, num_components):
                services = config_store.get(
                    f'node>{node_id}>components[{comp_idx}]>services')
                service = 'all' if services is None else ','.join(services)
                comp_name = components[comp_idx]['name']
                cmd = (f"/opt/seagate/cortx/{comp_name}/bin/{comp_name}_setup {interface}"
                       f" --config {config_store_url} --services {service}")
                Log.info(f"{cmd}")
                cmd_proc = SimpleProcess(cmd)
                _, err, rc = cmd_proc.run()
                if rc != 0 or err.decode('utf-8') != '':
                    CortxProvisioner._update_provisioning_info(
                        config_store, node_id, 'deployment', 'error')
                    raise CortxProvisionerError(
                        rc, "%s phase of %s, failed. %s", interface,
                        components[comp_idx]['name'], err)

                CortxProvisioner._update_provisioning_info(
                    config_store, node_id, 'deployment', 'progress')

        CortxProvisioner._update_provisioning_info(
            config_store, node_id, 'deployment', 'success')

        Log.info(f'Finished cluster bootstrap on {node_id}:{node_name}')

    @staticmethod
    def _update_provisioning_info(config_store, node_id, phase, status='default'):
        """Add phase, status, version, release keys in conf_stor.

            args:
            config_store: config store url. eg. yaml:///etc/cortx/cluster.conf
            node_id: machine-id
            phase: deployment/upgrade
            status: default/progress/success/error."""
        key_prefix = f'node>{node_id}>provisioning>'
        keys = [(key_prefix + 'phase', phase), (key_prefix + 'status', status)]
        config_store.set_kvs(keys)

