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
from enum import Enum
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


class PROVISIONING_STAGES(Enum):
    DEPLOYMENT = "deployment"
    UPGRADE = "upgrade"


class PROVISIONING_STATUS(Enum):
    DEFAULT = "default"
    ERROR = "error"
    PROGRESS = "progress"
    SUCCESS = "success"


class CortxProvisioner:
    """ CORTX Provosioner """

    _cortx_conf_url = "yaml:///etc/cortx/cluster.conf"
    _solution_index = "solution_conf"
    _secrets_path = "/etc/cortx/solution/secret"
    _rel_secret_path = "/solution/secret"
    cortx_release = CortxRelease()

    @staticmethod
    def init():
        pass

    @staticmethod
    def config_apply(solution_config_url: str, cortx_conf_url: str = None,
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

        if cortx_conf_url is None:
            cortx_conf_url = CortxProvisioner._cortx_conf_url
        cortx_conf = ConfigStore(cortx_conf_url)

        # Check if config is already applied on node.
        node_id = Conf.machine_id
        if cortx_conf.get(f'node>{node_id}>provisioning>version') and force_override is False:
            Log.info('CORTX config already applied on this node.')
            return 0

        # Load same config again if force_override is True
        try:
            cs_option = {"fail_reload": False} if force_override else {"skip_reload": True}
            Log.info('Applying config %s' % solution_config_url)
            Conf.load(CortxProvisioner._solution_index, solution_config_url,
                **cs_option)
        except ConfError as e:
            Log.error(f'Unable to load {solution_config_url} url, Error:{e}')

        # Secrets path from config file
        if cortx_conf.get('cortx>common>storage>local'):
            CortxProvisioner.secrets_path = cortx_conf.get('cortx>common>storage>local')+CortxProvisioner._rel_secret_path

        # source code for encrypting and storing secret key
        if Conf.get(CortxProvisioner._solution_index, 'cluster') is not None:
            CortxProvisioner.apply_cluster_config(cortx_conf, CortxProvisioner.cortx_release)

        if Conf.get(CortxProvisioner._solution_index, 'cortx') is not None:
            # generating cipher key
            cipher_key = None
            cluster_id = Conf.get(CortxProvisioner._solution_index, 'cluster>id')
            if cluster_id is None:
                cluster_id = cortx_conf.get('cluster>id')
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
            CortxProvisioner.apply_cortx_config(cortx_conf, CortxProvisioner.cortx_release)

    @staticmethod
    def apply_cortx_config(cortx_conf, cortx_release):
        """ Convert CORTX config into confstore keys """
        config_info = Conf.get(CortxProvisioner._solution_index, 'cortx')
        cortx_solution_config = CortxConfig(config_info, cortx_release)
        cortx_solution_config.save(cortx_conf, CortxProvisioner._solution_index)

    @staticmethod
    def apply_cluster_config(cortx_conf, cortx_release):
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
            cortx_conf.set_kvs(cluster_keys)

            nodes = []
            for storage_set in storage_sets:
                for node in storage_set['nodes']:
                    node_type = node['type']
                    node = dict(node_map[node_type], **node)
                    node['storage_set'] = storage_set['name']
                    node['cluster_id'] = cluster_id
                    nodes.append(node)

            solution_config_nodes = CortxCluster(nodes, cortx_release)
            solution_config_nodes.save(cortx_conf)
            solution_config_storagesets = CortxStorageSet(storage_sets)
            solution_config_storagesets.save(cortx_conf)
        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while applying cluster_config {e}')

    @staticmethod
    def _get_node_info(cortx_conf: ConfigStore):
        """To get the node information."""
        node_id = Conf.machine_id
        if node_id is None:
            raise CortxProvisionerError(errno.EINVAL, "Invalid node_id: %s", \
                node_id)

        # Reinitialize logging with configured log path
        log_path = os.path.join(
            cortx_conf.get('cortx>common>storage>log'), const.APP_NAME, node_id)
        log_level = os.getenv('CORTX_PROVISIONER_DEBUG_LEVEL', const.DEFAULT_LOG_LEVEL)
        CortxProvisionerLog.reinitialize(
            const.SERVICE_NAME, log_path, level=log_level)

        if cortx_conf.get(f'node>{node_id}>name') is None:
            raise CortxProvisionerError(
                errno.EINVAL, f'Node name not found in cortx config for node {node_id}.')

        node_name = cortx_conf.get(f'node>{node_id}>name')

        return node_id, node_name

    @staticmethod
    def _provision_components(cortx_conf: ConfigStore, mini_prov_interfaces: list, apply_phase: str):
        """Invoke Mini Provisioners of cluster components."""
        node_id, node_name = CortxProvisioner._get_node_info(cortx_conf)
        num_components = int(cortx_conf.get(f'node>{node_id}>num_components'))
        for interface in mini_prov_interfaces:
            for comp_idx in range(0, num_components):
                key_prefix = f'node>{node_id}>components[{comp_idx}]'
                component_name = cortx_conf.get(f'{key_prefix}>name')
                # Get services.
                service_idx = 0
                services = []
                while (cortx_conf.get(f'{key_prefix}>services[{service_idx}]') is not None):
                    services.append(cortx_conf.get(f'{key_prefix}>services[{service_idx}]'))
                    service_idx = service_idx + 1
                service = 'all' if service_idx == 0 else ','.join(services)
                if apply_phase == PROVISIONING_STAGES.UPGRADE.value:
                    version = cortx_conf.get(f'{key_prefix}>version')
                    # Skip update for component if it is already updated.
                    is_updated = CortxProvisioner._is_component_updated(component_name, version)
                    if is_updated is True:
                        Log.info(f'{component_name} is already updated with {version} version.')
                        continue
                CortxProvisioner._update_provisioning_status(
                        cortx_conf, node_id, apply_phase, PROVISIONING_STATUS.PROGRESS.value)
                cmd = (
                    f"/opt/seagate/cortx/{component_name}/bin/{component_name}_setup {interface}"
                    f" --config {cortx_conf._conf_url} --services {service}")
                Log.info(f"{cmd}")
                cmd_proc = SimpleProcess(cmd)
                _, err, rc = cmd_proc.run()
                if rc != 0:
                    CortxProvisioner._update_provisioning_status(
                        cortx_conf, node_id, apply_phase, PROVISIONING_STATUS.ERROR.value)
                    raise CortxProvisionerError(
                        rc, "%s phase of %s, failed. %s", interface,
                        component_name, err)
                # Update version for each component if upgrade successful.
                if apply_phase == PROVISIONING_STAGES.UPGRADE.value:
                    component_version = CortxProvisioner.cortx_release.get_version(component_name)
                    cortx_conf.set(f'{key_prefix}>version', component_version)
        CortxProvisioner._update_provisioning_status(
            cortx_conf, node_id, apply_phase, PROVISIONING_STATUS.SUCCESS.value)

    @staticmethod
    def cluster_bootstrap(cortx_conf_url: str, force_override: bool = False):
        """
        Description:
        Configures Cluster Components
        1. Reads Cortx Config and obtain cluster components
        2. Invoke Mini Provisioners of cluster components
        Paramaters:
        [IN] CORTX Config URL
        """
        cortx_conf = ConfigStore(cortx_conf_url)
        apply_phase = PROVISIONING_STAGES.DEPLOYMENT.value
        node_id, node_name = CortxProvisioner._get_node_info(cortx_conf)
        is_valid, ret_code = CortxProvisioner._validate_provisioning_status(
            cortx_conf, node_id, apply_phase)
        if is_valid is False:
            if force_override is False:
                Log.warn('Validation check failed, Aborting cluster bootstarp'
                    f' with return code {ret_code}')
                return ret_code
            else:
                Log.info('Validation check failed, Forcefully overriding deployment.')
        Log.info(f"Starting cluster bootstrap on {node_id}:{node_name}")
        CortxProvisioner._update_provisioning_status(
            cortx_conf, node_id, apply_phase)
        mini_prov_interfaces = ['post_install', 'prepare', 'config', 'init']
        CortxProvisioner._provision_components(cortx_conf, mini_prov_interfaces, apply_phase)
        CortxProvisioner._add_version_info(cortx_conf, node_id)
        Log.info(f"Finished cluster bootstrap on {node_id}:{node_name}")

    @staticmethod
    def cluster_upgrade(cortx_conf_url: str, force_override: bool = False):
        """
        Description:
        Upgrades Cluster Components
        1. Reads Cortx Config and obtain cluster components
        2. Invoke upgrade phase of cluster components
        Paramaters:
        [IN] CORTX Config URL
        """
        cortx_conf = ConfigStore(cortx_conf_url)
        apply_phase = PROVISIONING_STAGES.UPGRADE.value
        node_id, node_name = CortxProvisioner._get_node_info(cortx_conf)
        is_valid, ret_code = CortxProvisioner._validate_provisioning_status(
            cortx_conf, node_id, apply_phase)
        if is_valid is False:
            if force_override is False:
                Log.warn('Validation check failed, Aborting upgrade with '
                    f'return code {ret_code}.')
                return ret_code
            else:
                Log.info('Validation check failed, Forcefully overriding upgrade.')

        Log.info(f"Starting cluster upgrade on {node_id}:{node_name}")
        CortxProvisioner._update_provisioning_status(
            cortx_conf, node_id, apply_phase)

        mini_prov_interfaces = ['upgrade']
        CortxProvisioner._provision_components(cortx_conf, mini_prov_interfaces, apply_phase)
        # Update CORTX version, once the upgrade is successful
        CortxProvisioner._add_version_info(cortx_conf, node_id)
        Log.info(f"Finished cluster upgrade on {node_id}:{node_name}")

    @staticmethod
    def _update_provisioning_status(cortx_conf: ConfigStore, node_id: str,
        phase: str, status: str = PROVISIONING_STATUS.DEFAULT.value):
        """
        Description
        Add phase, status, version, release keys in confstore.
        Args:
        cortx_conf: config store url. eg. yaml:///etc/cortx/cluster.conf
        node_id: machine-id
        phase: deployment/upgrade
        status: default/progress/success/error."""
        key_prefix = f'node>{node_id}>provisioning>'
        keys = [(key_prefix + 'phase', phase), (key_prefix + 'status', status)]
        cortx_conf.set_kvs(keys)

    @staticmethod
    def _is_component_updated(component_name: str, component_version: str):
        """Verify component version with RELEASE.INFO."""
        release_version = CortxProvisioner.cortx_release.get_version(component_name)
        return True if release_version == component_version else False

    @staticmethod
    def _add_version_info(cortx_conf: ConfigStore, node_id):
        """Add version in confstore."""
        version = CortxProvisioner.cortx_release.get_value('VERSION')
        cortx_conf.set('cortx>common>release>version', version)
        cortx_conf.set(f'node>{node_id}>provisioning>version', version)

    @staticmethod
    def _validate_provisioning_status(cortx_conf: ConfigStore, node_id: str, apply_phase: str):
        """Validate provisioning."""
        ret_code = 0
        recent_phase = cortx_conf.get(f'node>{node_id}>provisioning>phase')
        recent_status = cortx_conf.get(f'node>{node_id}>provisioning>status')
        msg = f'Recent phase for this node is {recent_phase} and ' + \
                f'recent status is {recent_status}. '
        # {apply_phase: {recent_phase: {recent_status: [boolean_result,rc]}}}
        validations_checks = {
            PROVISIONING_STAGES.DEPLOYMENT.value: {
                PROVISIONING_STAGES.DEPLOYMENT.value: {
                    PROVISIONING_STATUS.DEFAULT.value: [True, 0],
                    PROVISIONING_STATUS.ERROR.value: [True, 0],
                    PROVISIONING_STATUS.PROGRESS.value: [True, 0],
                    PROVISIONING_STATUS.SUCCESS.value: [False, 0]
                },
                PROVISIONING_STAGES.UPGRADE.value: {
                    PROVISIONING_STATUS.DEFAULT.value: [True, 0],
                    PROVISIONING_STATUS.ERROR.value: [True, 0],
                    PROVISIONING_STATUS.PROGRESS.value: [True, 0],
                    PROVISIONING_STATUS.SUCCESS.value: [True, 0]
                }},
            PROVISIONING_STAGES.UPGRADE.value: {
                PROVISIONING_STAGES.DEPLOYMENT.value: {
                    PROVISIONING_STATUS.DEFAULT.value: [False, 1],
                    PROVISIONING_STATUS.ERROR.value: [False, 1],
                    PROVISIONING_STATUS.PROGRESS.value: [False, 1],
                    PROVISIONING_STATUS.SUCCESS.value: [True, 0]
                },
                PROVISIONING_STAGES.UPGRADE.value: {
                    PROVISIONING_STATUS.DEFAULT.value: [True, 0],
                    PROVISIONING_STATUS.ERROR.value: [True, 0],
                    PROVISIONING_STATUS.PROGRESS.value: [True, 0],
                    PROVISIONING_STATUS.SUCCESS.value: [True, 0]
                }
            }}
        if recent_phase is None and recent_status is None:
            Log.info(msg + f'Performing {apply_phase} on this node.')
            return True, ret_code

        if (not validations_checks.get(apply_phase) or
            not validations_checks.get(apply_phase).get(recent_phase) or
            not validations_checks.get(apply_phase).get(recent_phase).get(recent_status)):
            Log.error('Invalid phase or status.')
            ret_code = 1
            return False, ret_code

        validate_result = validations_checks.get(apply_phase).get(recent_phase).get(recent_status)
        if validate_result[1] != 0:
            Log.error(msg + f'{apply_phase} is not possible on this node.')
            if apply_phase == PROVISIONING_STAGES.UPGRADE.value:
                # Reset status.
                recent_status = cortx_conf.set(f'node>{node_id}>provisioning>status',
                    PROVISIONING_STATUS.DEFAULT.value)
        else:
            Log.info(msg)
        return validate_result[0], validate_result[1]
