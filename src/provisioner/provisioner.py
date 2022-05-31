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
from cortx.utils.conf_store import Conf, MappedConf
from cortx.utils.security.cipher import Cipher
from cortx.utils.schema.release import Release
from cortx.provisioner import const
from cortx.provisioner.log import CortxProvisionerLog, Log
from cortx.provisioner.error import CortxProvisionerError
from cortx.utils.conf_store.error import ConfError
from cortx.provisioner.config import CortxConfig
from cortx.provisioner.cluster import CortxCluster, CortxStorageSet


class ProvisionerStages(Enum):
    DEPLOYMENT = "deployment"
    UPGRADE = "upgrade"

class DeploymentInterfaces(Enum):
    POST_INSTALL= "post_install"
    PREAPRE= "prepare"
    CONFIG= "config"
    INIT= "init"

class UpgradeInterfaces(Enum):
    UPGRADE = "upgrade"

class ProvisionerStatus(Enum):
    DEFAULT = "default"
    ERROR = "error"
    PROGRESS = "progress"
    SUCCESS = "success"


class CortxProvisioner:
    """CORTX Provosioner."""
    _cortx_conf_url = "yaml:///etc/cortx/cluster.conf"
    _solution_index = "solution_conf"
    _tmp_index = "temp_conf"
    _delta_index = "delta_index"
    _conf_index = "conf_index"
    _secrets_path = "/etc/cortx/solution/secret"
    _rel_secret_path = "/solution/secret"
    _cortx_gconf_consul_index = "consul_index"
    _tmp_cortx_conf_url = "yaml:///tmp/tmp.conf"
    cortx_release = Release(const.RELEASE_INFO_URL)

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
        cortx_conf = MappedConf(CortxProvisioner._tmp_cortx_conf_url)

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
            CortxProvisioner._secrets_path = cortx_conf.get('cortx>common>storage>local')+CortxProvisioner._rel_secret_path

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
            # Adding array count key in conf
            cortx_conf.add_num_keys()
            Conf.save(cortx_conf._conf_idx)

    @staticmethod
    def apply_cortx_config(cortx_conf, cortx_release):
        """Convert CORTX config into confstore keys"""
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
                        "One of the key [id, name,storage_sets,node_types] is unspecified for cluster.")

            for node_type in node_types:
                node_map[node_type['name']] = node_type
            cluster_keys = [('cluster>id', cluster_id),
                ('cluster>name', cluster_name)]
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
    def _get_node_info(_conf_idx: str):
        """To get the node information."""
        node_id = Conf.machine_id
        if node_id is None:
            raise CortxProvisionerError(errno.EINVAL, "Invalid node_id: %s", \
                node_id)

        # Reinitialize logging with configured log path
        log_path = os.path.join(
            Conf.get(_conf_idx, 'cortx>common>storage>log'), const.APP_NAME, node_id)
        log_level = os.getenv('CORTX_PROVISIONER_DEBUG_LEVEL', const.DEFAULT_LOG_LEVEL)
        CortxProvisionerLog.reinitialize(
            const.SERVICE_NAME, log_path, level=log_level)

        if Conf.get(_conf_idx, f'node>{node_id}>name') is None:
            raise CortxProvisionerError(
                errno.EINVAL, f'Node name not found in cortx config for node {node_id}.')

        node_name = Conf.get(_conf_idx, f'node>{node_id}>name')

        return node_id, node_name

    @staticmethod
    def _provision_components(cortx_conf_url: str, _conf_idx: str, interfaces: Enum, apply_phase: str):
        """Invoke Mini Provisioners of cluster components."""
        node_id, _ = CortxProvisioner._get_node_info(_conf_idx)
        num_components = int(Conf.get(_conf_idx, f'node>{node_id}>num_components'))
        for interface in interfaces:
            for comp_idx in range(0, num_components):
                key_prefix = f'node>{node_id}>components[{comp_idx}]'
                component_name = Conf.get(_conf_idx, f'{key_prefix}>name')
                # Check if RPM exists for the component, if it does exist get the build version
                component_version = CortxProvisioner.cortx_release.get_component_version(
                    component_name)
                # Get services.
                service_idx = 0
                services = []
                while (Conf.get(_conf_idx, f'{key_prefix}>services[{service_idx}]') is not None):
                    services.append(Conf.get(_conf_idx, f'{key_prefix}>services[{service_idx}]'))
                    service_idx = service_idx + 1
                service = 'all' if service_idx == 0 else ','.join(services)
                if apply_phase == ProvisionerStages.UPGRADE.value:
                    version = Conf.get(_conf_idx, f'{key_prefix}>version')
                    # Skip update for component if it is already updated.
                    is_updated = CortxProvisioner._is_component_updated(component_name, version)
                    if is_updated is True:
                        Log.info(f'{component_name} is already updated with {version} version.')
                        continue
                CortxProvisioner._update_provisioning_status(
                        _conf_idx, node_id, apply_phase, ProvisionerStatus.PROGRESS.value)
                if interface.value == 'upgrade':
                    # TODO: add --changeset parameter once all components support config upgrade
                    cmd = (
                        f"/opt/seagate/cortx/{component_name}/bin/{component_name}_setup {interface.value}"
                        f" --config {cortx_conf_url} --services {service}")
                else:
                    cmd = (
                        f"/opt/seagate/cortx/{component_name}/bin/{component_name}_setup {interface.value}"
                        f" --config {cortx_conf_url} --services {service}")
                Log.info(f"{cmd}")
                cmd_proc = SimpleProcess(cmd)
                _, err, rc = cmd_proc.run()
                if rc != 0:
                    CortxProvisioner._update_provisioning_status(
                        _conf_idx, node_id, apply_phase, ProvisionerStatus.ERROR.value)
                    raise CortxProvisionerError(
                        rc, "%s phase of %s, failed. %s", interface.value,
                        component_name, err)

                # Update version for each component if Provisioning successful.
                Conf.set(_conf_idx, f'{key_prefix}>version', component_version)

    @staticmethod
    def _apply_consul_config(_conf_idx: str):
        num_endpoints = Conf.get(_conf_idx, 'cortx>external>consul>num_endpoints')
        for idx in range(0, num_endpoints):
            if 'http' in Conf.get(_conf_idx, f'cortx>external>consul>endpoints[{idx}]'):
                consul_endpoint = Conf.get(_conf_idx, f'cortx>external>consul>endpoints[{idx}]')
                break
        gconf_consul_url = consul_endpoint.replace('http','consul') + '/conf'
        Conf.load(CortxProvisioner._cortx_gconf_consul_index, gconf_consul_url)
        Conf.copy(_conf_idx, CortxProvisioner._cortx_gconf_consul_index, Conf.get_keys(_conf_idx))
        Conf.save(CortxProvisioner._cortx_gconf_consul_index)
        # TODO: place the below code at a proper location when this function is removed.
        with open(const.CONSUL_CONF_URL, 'w') as f:
            f.write(gconf_consul_url)

    @staticmethod
    def cluster_bootstrap(cortx_conf_url: str, force_override: bool = False):
        """
        Description:

        Configures Cluster Components
        1. Compares current installed version with New version
        2. Invoke Mini Provisioners of cluster components deploy/upgrade based on version compatibility
        Paramaters:
        [IN] CORTX Config URL
        """
        Conf.load(CortxProvisioner._conf_index, cortx_conf_url)
        Conf.load(CortxProvisioner._tmp_index, CortxProvisioner._tmp_cortx_conf_url)
        tmp_conf_keys = Conf.get_keys(CortxProvisioner._tmp_index)
        node_id = Conf.machine_id
        installed_version = Conf.get(CortxProvisioner._conf_index, f'node>{node_id}>provisioning>version')
        release_version = CortxProvisioner.cortx_release.get_release_version()
        if installed_version is None:
            Conf.copy(CortxProvisioner._tmp_index, CortxProvisioner._conf_index, tmp_conf_keys)
            Conf.save(CortxProvisioner._conf_index)
            CortxProvisioner._apply_consul_config(CortxProvisioner._conf_index)
            CortxProvisioner.cluster_deploy(cortx_conf_url, force_override)
        else:
            # TODO: add a case where release_version > installed_version but is not compatible.
            ret_code = CortxProvisioner.cortx_release.version_check(
                release_version, installed_version)
            if ret_code == 1:
                CortxProvisioner._prepare_diff(CortxProvisioner._conf_index, CortxProvisioner._tmp_index, CortxProvisioner._delta_index)
                CortxProvisioner.cluster_upgrade(cortx_conf_url, force_override)
                # TODO: update_conf needs to be removed once gconf moves to consul.
                # Gconf update after upgrade should not be handled here if gconf is in consul.
                CortxProvisioner._update_conf(CortxProvisioner._conf_index, CortxProvisioner._tmp_index)
            # TODO: This will be removed once downgrade is also supported.
            elif ret_code == -1:
                raise CortxProvisionerError(errno.EINVAL, 'Downgrade is Not Supported')
            elif ret_code == 0:
                Conf.copy(CortxProvisioner._tmp_index, CortxProvisioner._conf_index, tmp_conf_keys)
                Conf.save(CortxProvisioner._conf_index)
                CortxProvisioner.cluster_deploy(cortx_conf_url, force_override)
            else:
                raise CortxProvisionerError(errno.EINVAL, 'Internal error. Could not determine version. Invalid image.')

    @staticmethod
    def cluster_deploy(cortx_conf_url: str, force_override: bool = False):
        """
        Description:
        Configures Cluster Components
        1. Reads Cortx Config and obtain cluster components
        2. Invoke Mini Provisioners of cluster components
        Paramaters:
        [IN] CORTX Config URL
        """
        apply_phase = ProvisionerStages.DEPLOYMENT.value
        node_id, node_name = CortxProvisioner._get_node_info(CortxProvisioner._conf_index)
        is_valid, ret_code = CortxProvisioner._validate_provisioning_status(
            CortxProvisioner._conf_index, node_id, apply_phase)
        if is_valid is False:
            if force_override is False:
                Log.warn('Validation check failed, Aborting cluster bootstarp'
                    f' with return code {ret_code}')
                return ret_code
            else:
                Log.info('Validation check failed, Forcefully overriding deployment.')
        Log.info(f"Starting cluster bootstrap on {node_id}:{node_name}")
        CortxProvisioner._update_provisioning_status(
            CortxProvisioner._conf_index, node_id, apply_phase)
        CortxProvisioner._provision_components(cortx_conf_url, CortxProvisioner._conf_index, DeploymentInterfaces, apply_phase)
        CortxProvisioner._add_version_info(CortxProvisioner._conf_index, node_id)
        CortxProvisioner._update_provisioning_status(
            CortxProvisioner._conf_index, node_id, apply_phase, ProvisionerStatus.SUCCESS.value)
        Log.info(f"Finished cluster bootstrap on {node_id}:{node_name}")

    @staticmethod
    def _prepare_diff(idx1: str, idx2: str, diff_idx: str):
        """
        Description:
        Compare two conf index and prepare delta diff config.
        1. Fetch new/deleted/updated keys by comparing idx1 and idx2
        2. Prepare delta config on diff_index
        Paramaters:
        [idx1] conf index 1
        [idx2] conf index 2
        [diff_idx] delta diff index
        """
        new_keys, deleted_keys, changed_keys = Conf.compare(idx1, idx2)
        Conf.load(diff_idx, const.CORTX_DELTA_URL)
        for key in new_keys:
            Conf.set(diff_idx, f'new>{key}', Conf.get(idx2, key))
        for key in deleted_keys:
            Conf.set(diff_idx, f'deleted>{key}', Conf.get(idx1, key))
        for key in changed_keys:
            value = f"{Conf.get(idx1, key)}|{Conf.get(idx2, key)}"
            Conf.set(diff_idx, f'changed>{key}', value)
        Conf.save(diff_idx)

    @staticmethod
    def _update_conf(_conf_idx: str, _tmp_idx: str):
        """
        Description:
        Updates conf by updating new keys/values post upgrade.
        1. Fetch new keys using conf compare
        2. Update gconf by adding new keys.
        3. Update gconf by updating changed values for cortx>common
        """
        new_keys, _, changed_keys = Conf.compare(_conf_idx, _tmp_idx)
        for key in new_keys:
            value= Conf.get(_tmp_idx, key)
            Conf.set(_conf_idx, key, value)
        for key in changed_keys:
            if key.startswith('cortx>common'):
                value= Conf.get(_tmp_idx, key)
                Conf.set(_conf_idx, key, value)
        Conf.save(_conf_idx)

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
        # query to get cluster health
        upgrade_mode = os.getenv(const.UPGRADE_MODE_KEY, const.UPGRADE_MODE_VAL).upper()
        if upgrade_mode != "COLD" and not CortxProvisioner.is_cluster_healthy():
            Log.error('Cluster is unhealthy, Aborting upgrade with return code 1')
            return 1
        apply_phase = ProvisionerStages.UPGRADE.value
        node_id, node_name = CortxProvisioner._get_node_info(CortxProvisioner._conf_index)
        is_valid, ret_code = CortxProvisioner._validate_provisioning_status(
            CortxProvisioner._conf_index, node_id, apply_phase)
        if is_valid is False:
            if force_override is False:
                Log.warn('Validation check failed, Aborting upgrade with '
                    f'return code {ret_code}.')
                return ret_code
            else:
                Log.info('Validation check failed, Forcefully overriding upgrade.')

        Log.info(f"Starting cluster upgrade on {node_id}:{node_name}")
        CortxProvisioner._update_provisioning_status(
            CortxProvisioner._conf_index, node_id, apply_phase)

        CortxProvisioner._provision_components(cortx_conf_url, CortxProvisioner._conf_index, UpgradeInterfaces, apply_phase)
        # Update CORTX version, once the upgrade is successful
        CortxProvisioner._add_version_info(CortxProvisioner._conf_index, node_id)
        CortxProvisioner._update_provisioning_status(
            CortxProvisioner._conf_index, node_id, apply_phase, ProvisionerStatus.SUCCESS.value)
        Log.info(f"Finished cluster upgrade on {node_id}:{node_name}")

    @staticmethod
    def _update_provisioning_status(_conf_idx: str, node_id: str,
        phase: str, status: str = ProvisionerStatus.DEFAULT.value):
        """
        Description:

        Add phase, status, version, release keys in confstore.
        Args:
        cortx_conf: config store url. eg. yaml:///etc/cortx/cluster.conf
        node_id: machine-id
        phase: deployment/upgrade
        status: default/progress/success/error."""
        key_prefix = f'node>{node_id}>provisioning'
        Conf.set(_conf_idx, f'{key_prefix}>phase', phase)
        Conf.set(_conf_idx, f'{key_prefix}>status', status)
        Conf.save(_conf_idx)
        # TODO: Remove the following section once gconf is moved to consul completely.
        _idx = CortxProvisioner._cortx_gconf_consul_index
        if phase.upper() == 'UPGRADE':
            with open(const.CONSUL_CONF_URL, 'r') as f:
                gconf_consul_url = f.read().strip()
            _idx = 'consul_upgrade_idx'
            if status == ProvisionerStatus.DEFAULT.value:
                Conf.load(_idx, gconf_consul_url)
        Conf.set(_idx, f'{key_prefix}>phase', phase)
        Conf.set(_idx, f'{key_prefix}>status', status)
        Conf.save(_idx)

    @staticmethod
    def _is_component_updated(component_name: str, deploy_version: str):
        """Check deployed and release component version."""
        is_updated = True
        comp_release_version = CortxProvisioner.cortx_release.get_component_version(
            component_name)
        ret_code = CortxProvisioner.cortx_release.version_check(
            deploy_version, comp_release_version)
        if ret_code == -1:
            is_updated = False
        return is_updated

    @staticmethod
    def _add_version_info(_conf_idx: str, node_id):
        """Add version in confstore."""
        version = CortxProvisioner.cortx_release.get_release_version()
        Conf.set(_conf_idx, 'cortx>common>release>version', version)
        Conf.set(_conf_idx, f'node>{node_id}>provisioning>version', version)

    @staticmethod
    def _validate_provisioning_status(_conf_idx: str, node_id: str, apply_phase: str):
        """Validate provisioning."""
        ret_code = 0
        recent_phase = Conf.get(_conf_idx, f'node>{node_id}>provisioning>phase')
        recent_status = Conf.get(_conf_idx, f'node>{node_id}>provisioning>status')
        msg = f'Recent phase for this node is {recent_phase} and ' + \
                f'recent status is {recent_status}. '
        # {apply_phase: {recent_phase: {recent_status: [boolean_result,rc]}}}
        validations_checks = {
            ProvisionerStages.DEPLOYMENT.value: {
                ProvisionerStages.DEPLOYMENT.value: {
                    ProvisionerStatus.DEFAULT.value: [True, 0],
                    ProvisionerStatus.ERROR.value: [True, 0],
                    ProvisionerStatus.PROGRESS.value: [True, 0],
                    ProvisionerStatus.SUCCESS.value: [False, 0]
                },
                ProvisionerStages.UPGRADE.value: {
                    ProvisionerStatus.DEFAULT.value: [True, 0],
                    ProvisionerStatus.ERROR.value: [True, 0],
                    ProvisionerStatus.PROGRESS.value: [True, 0],
                    ProvisionerStatus.SUCCESS.value: [True, 0]
                }},
            ProvisionerStages.UPGRADE.value: {
                ProvisionerStages.DEPLOYMENT.value: {
                    ProvisionerStatus.DEFAULT.value: [False, 1],
                    ProvisionerStatus.ERROR.value: [False, 1],
                    ProvisionerStatus.PROGRESS.value: [False, 1],
                    ProvisionerStatus.SUCCESS.value: [True, 0]
                },
                ProvisionerStages.UPGRADE.value: {
                    ProvisionerStatus.DEFAULT.value: [True, 0],
                    ProvisionerStatus.ERROR.value: [True, 0],
                    ProvisionerStatus.PROGRESS.value: [True, 0],
                    ProvisionerStatus.SUCCESS.value: [True, 0]
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
            if apply_phase == ProvisionerStages.UPGRADE.value:
                # Reset status.
                recent_status = Conf.set(_conf_idx, f'node>{node_id}>provisioning>status',
                    ProvisionerStatus.DEFAULT.value)
        else:
            Log.info(msg)
        return validate_result[0], validate_result[1]

    @staticmethod
    def is_cluster_healthy():
        health = CortxProvisioner._get_resource_health(resource="cortx")
        return True if health == "OK" else False

    @staticmethod
    def _get_resource_health(resource:str):
        """API call to get cluster health."""
        # TODO Make a call to HA Health API to get the resource status
        return "OK"
