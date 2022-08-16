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

from datetime import datetime
import errno
import os
import time
import socket
from enum import Enum
import time
from urllib.parse import urlparse
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
    _secrets_path = "/etc/cortx/solution/secret"
    _rel_secret_path = "/solution/secret"
    _cortx_gconf_consul_index = "consul_index"
    _lock_domain = "provisioner"
    _timeout = 25
    _duration = 20
    _sleep = 2
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

        # Check if consul endpoint is reachable
        if 'consul' in cortx_conf_url:
            if not CortxProvisioner._check_consul_connection(cortx_conf_url, CortxProvisioner._timeout):
                raise CortxProvisionerError(errno.EINVAL, f"Consul endpoint {cortx_conf_url} not reachable over network")

        cortx_conf = MappedConf(cortx_conf_url)

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

        machine_id = CortxProvisioner._get_machine_id()
        if not CortxProvisioner._wait_for_lock_to_be_released(cortx_conf, CortxProvisioner._timeout, machine_id):
            if not Conf.unlock(cortx_conf._conf_idx, owner=machine_id, force = True, domain=CortxProvisioner._lock_domain):
                raise CortxProvisionerError(errno.EINVAL, f"Force unlock failed for index {cortx_conf._conf_idx}")
            # TODO: remove Conf.save once gconf is completly moved to consul
            Conf.save(cortx_conf._conf_idx)
        if cortx_conf.get('cortx>common>storage>local') is None and Conf.get(CortxProvisioner._solution_index, 'cortx') is not None:
            if not Conf.lock(cortx_conf._conf_idx, owner=machine_id, domain=CortxProvisioner._lock_domain, duration=CortxProvisioner._duration):
                raise CortxProvisionerError(errno.EINVAL, f"locking failed for index {cortx_conf._conf_idx}")
            # TODO: remove Conf.save once gconf is completly moved to consul
            Conf.save(cortx_conf._conf_idx)
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
            if not Conf.unlock(cortx_conf._conf_idx, owner=machine_id, domain=CortxProvisioner._lock_domain):
                raise CortxProvisionerError(errno.EINVAL, f"unlocking failed for index {cortx_conf._conf_idx}")
            # TODO: remove Conf.save once gconf is completly moved to consul
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
            machine_id = CortxProvisioner._get_machine_id()
            if not CortxProvisioner._wait_for_lock_to_be_released(cortx_conf, CortxProvisioner._timeout, machine_id):
                if not Conf.unlock(cortx_conf._conf_idx, owner=machine_id, force = True, domain=CortxProvisioner._lock_domain):
                    raise CortxProvisionerError(errno.EINVAL, f"Force unlock failed for index {cortx_conf._conf_idx}")
                # TODO: remove Conf.save once gconf is completly moved to consul
                Conf.save(cortx_conf._conf_idx)
            if cortx_conf.get('cluster>id') is None:
                cluster_keys = [('cluster>id', cluster_id),
                    ('cluster>name', cluster_name)]
                cortx_conf.set_kvs(cluster_keys)
                if not Conf.lock(cortx_conf._conf_idx, owner=machine_id, domain=CortxProvisioner._lock_domain, duration=CortxProvisioner._duration):
                    raise CortxProvisionerError(errno.EINVAL, f"locking failed for index {cortx_conf._conf_idx}")
                # TODO: remove Conf.save once gconf is completly moved to consul
                Conf.save(cortx_conf._conf_idx)
                solution_config_storagesets = CortxStorageSet(storage_sets)
                solution_config_storagesets.save(cortx_conf)
                Conf.save(cortx_conf._conf_idx)
                if not Conf.unlock(cortx_conf._conf_idx, owner=machine_id, domain=CortxProvisioner._lock_domain):
                    raise CortxProvisionerError(errno.EINVAL, f"unlocking failed for index {cortx_conf._conf_idx}")
                # TODO: remove Conf.save once gconf is completly moved to consul
                Conf.save(cortx_conf._conf_idx)
        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while applying cluster_config {e}')

    @staticmethod
    def _check_consul_connection(cortx_conf_url: str, timeout: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(CortxProvisioner._sleep)
        host, path = (cortx_conf_url.split('//')[-1]).split(':')
        port = path.split('/')[0]
        ## wait logic for consul endpoint to be available
        while timeout > 0 :
            try:
                if sock.connect_ex((host, int(port))) == 0:
                    return True
            except Exception:
                Log.debug('Waiting for Consul to be ready..')
            time.sleep(CortxProvisioner._sleep)
            timeout -=1
        return False

    @staticmethod
    def _wait_for_lock_to_be_released(cortx_conf: MappedConf, timeout: int, machine_id: str):
        rc = False
        while timeout > 0:
            if Conf.test_lock(cortx_conf._conf_idx, domain=CortxProvisioner._lock_domain, owner=machine_id):
                rc = True
                break
            time.sleep(CortxProvisioner._sleep)
            timeout -=1
        return rc

    @staticmethod
    def _get_machine_id():
        return const.MACHINE_ID_PATH.read_text().strip()

    @staticmethod
    def _get_node_info(cortx_conf: MappedConf):
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
    def _provision_components(cortx_conf: MappedConf, interfaces: Enum, apply_phase: str):
        """Invoke Mini Provisioners of cluster components."""
        node_id, _ = CortxProvisioner._get_node_info(cortx_conf)
        num_components = int(cortx_conf.get(f'node>{node_id}>num_components'))
        for interface in interfaces:
            for comp_idx in range(0, num_components):
                key_prefix = f'node>{node_id}>components[{comp_idx}]'
                component_name = cortx_conf.get(f'{key_prefix}>name')
                # Check if RPM exists for the component, if it does exist get the build version
                component_version = CortxProvisioner.cortx_release.get_component_version(
                    component_name)
                # Get services.
                service_idx = 0
                services = []
                while (cortx_conf.get(f'{key_prefix}>services[{service_idx}]') is not None):
                    services.append(cortx_conf.get(f'{key_prefix}>services[{service_idx}]'))
                    service_idx = service_idx + 1
                service = 'all' if service_idx == 0 else ','.join(services)
                if apply_phase == ProvisionerStages.UPGRADE.value:
                    version = cortx_conf.get(f'{key_prefix}>version')
                    # Skip update for component if it is already updated.
                    is_updated = CortxProvisioner._is_component_updated(component_name, version)
                    if is_updated is True:
                        Log.info(f'{component_name} is already updated with {version} version.')
                        continue
                CortxProvisioner._update_provisioning_status(
                        cortx_conf, node_id, apply_phase, ProvisionerStatus.PROGRESS.value)
                if interface.value == 'upgrade':
                    # TODO: add --changeset parameter once all components support config upgrade
                    cmd = (
                        f"/opt/seagate/cortx/{component_name}/bin/{component_name}_setup {interface.value}"
                        f" --config {cortx_conf._conf_url} --services {service}")
                else:
                    cmd = (
                        f"/opt/seagate/cortx/{component_name}/bin/{component_name}_setup {interface.value}"
                        f" --config {cortx_conf._conf_url} --services {service}")
                Log.info(f"{cmd}")
                cmd_proc = SimpleProcess(cmd)
                _, err, rc = cmd_proc.run()
                if rc != 0:
                    CortxProvisioner._update_provisioning_status(
                        cortx_conf, node_id, apply_phase, ProvisionerStatus.ERROR.value)
                    raise CortxProvisionerError(
                        rc, "%s phase of %s, failed. %s", interface.value,
                        component_name, err)

                # Update version for each component if Provisioning successful.
                cortx_conf.set(f'{key_prefix}>version', component_version)

                # TODO: Remove the following code when gconf is completely moved to consul.
                CortxProvisioner._load_consul_conf(CortxProvisioner._cortx_gconf_consul_index)
                Conf.set(CortxProvisioner._cortx_gconf_consul_index,
                        f'{key_prefix}>version', component_version)
                Conf.save(CortxProvisioner._cortx_gconf_consul_index)

    @staticmethod
    def _apply_consul_config(cortx_conf: MappedConf):
        try:
            num_endpoints = int(cortx_conf.get('cortx>external>consul>num_endpoints'))
            if num_endpoints == 0:
                raise CortxProvisionerError(errno.EINVAL, f"Invalid value for num_endpoints '{num_endpoints}'")
            for idx in range(0, num_endpoints):
                consul_endpoint = cortx_conf.get(f'cortx>external>consul>endpoints[{idx}]')
                if not consul_endpoint:
                    raise CortxProvisionerError(errno.EINVAL, "Consul Endpoint can't be empty.")
                if urlparse(consul_endpoint).scheme not in ['http', 'https', 'tcp']:
                    raise CortxProvisionerError(errno.EINVAL, f"Invalid Consul Endpoint {consul_endpoint}")
                if 'http' in consul_endpoint:
                    break
        except ConfError as e:
            raise CortxProvisionerError(errno.EINVAL, f"Unable to get consul endpoint detail , Error:{e}")

        gconf_consul_url = consul_endpoint.replace('http','consul') + '/conf'
        # Check if consul endpoint is reachable
        if not CortxProvisioner._check_consul_connection(gconf_consul_url, CortxProvisioner._timeout):
            raise CortxProvisionerError(errno.EINVAL, f"Consul endpoint {gconf_consul_url} not reachable over network")
        Conf.load(CortxProvisioner._cortx_gconf_consul_index, gconf_consul_url)
        Conf.copy(cortx_conf._conf_idx, CortxProvisioner._cortx_gconf_consul_index, Conf.get_keys(cortx_conf._conf_idx))
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
        cortx_conf = MappedConf(cortx_conf_url)
        # TODO: Remove the following code when gconf is completely moved to consul.
        CortxProvisioner._apply_consul_config(cortx_conf)
        node_id = Conf.machine_id
        installed_version = cortx_conf.get(f'node>{node_id}>provisioning>version')
        release_version = CortxProvisioner.cortx_release.get_release_version()
        if installed_version is None:
            CortxProvisioner.cluster_deploy(cortx_conf_url, force_override)
        else:
            # TODO: add a case where release_version > installed_version but is not compatible.
            ret_code = CortxProvisioner.cortx_release.version_check(
                release_version, installed_version)
            if ret_code == 1:
                CortxProvisioner.cluster_upgrade(cortx_conf_url, force_override)
            # TODO: This will be removed once downgrade is also supported.
            elif ret_code == -1:
                raise CortxProvisionerError(errno.EINVAL, 'Downgrade is Not Supported')
            elif ret_code == 0:
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
        cortx_conf = MappedConf(cortx_conf_url)
        apply_phase = ProvisionerStages.DEPLOYMENT.value
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
        CortxProvisioner._provision_components(cortx_conf, DeploymentInterfaces, apply_phase)
        CortxProvisioner._add_version_info(cortx_conf, node_id)
        CortxProvisioner._update_provisioning_status(
            cortx_conf, node_id, apply_phase, ProvisionerStatus.SUCCESS.value)
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
        cortx_conf = MappedConf(cortx_conf_url)
        # query to get cluster health
        upgrade_mode = os.getenv(const.UPGRADE_MODE_KEY, const.UPGRADE_MODE_VAL).upper()
        if upgrade_mode != "COLD" and not CortxProvisioner.is_cluster_healthy():
            Log.error('Cluster is unhealthy, Aborting upgrade with return code 1')
            return 1
        apply_phase = ProvisionerStages.UPGRADE.value
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

        CortxProvisioner._provision_components(cortx_conf, UpgradeInterfaces, apply_phase)
        # Update CORTX version, once the upgrade is successful
        CortxProvisioner._add_version_info(cortx_conf, node_id)
        CortxProvisioner._update_provisioning_status(
            cortx_conf, node_id, apply_phase, ProvisionerStatus.SUCCESS.value)
        Log.info(f"Finished cluster upgrade on {node_id}:{node_name}")

    @staticmethod
    def _update_provisioning_status(cortx_conf: MappedConf, node_id: str,
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
        keys = [(key_prefix + '>' + 'phase', phase), (key_prefix + '>' + 'status', status)]
        cortx_conf.set_kvs(keys)

        # TODO: Remove the following section once gconf is moved to consul completely.
        CortxProvisioner._load_consul_conf(CortxProvisioner._cortx_gconf_consul_index)
        Conf.set(CortxProvisioner._cortx_gconf_consul_index, f'{key_prefix}>phase', phase)
        Conf.set(CortxProvisioner._cortx_gconf_consul_index, f'{key_prefix}>status', status)
        if phase is ProvisionerStages.DEPLOYMENT.value:
            cortx_conf.set(f'{key_prefix}>time', int(time.time()))
            Conf.set(CortxProvisioner._cortx_gconf_consul_index, f'{key_prefix}>time', int(time.time()))
        Conf.save(CortxProvisioner._cortx_gconf_consul_index)

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
    def _add_version_info(cortx_conf: MappedConf, node_id):
        """Add version in confstore."""
        version = CortxProvisioner.cortx_release.get_release_version()
        cortx_conf.set('cortx>common>release>version', version)
        cortx_conf.set(f'node>{node_id}>provisioning>version', version)

        # TODO: Remove the following sdection when gconf is completely moved to consul
        CortxProvisioner._load_consul_conf(CortxProvisioner._cortx_gconf_consul_index)
        Conf.set(CortxProvisioner._cortx_gconf_consul_index, 'cortx>common>release>version', version)
        Conf.set(CortxProvisioner._cortx_gconf_consul_index, f'node>{node_id}>provisioning>version', version)
        Conf.save(CortxProvisioner._cortx_gconf_consul_index)

    @staticmethod
    def _validate_provisioning_status(cortx_conf: MappedConf, node_id: str, apply_phase: str):
        """Validate provisioning."""
        ret_code = 0
        recent_phase = cortx_conf.get(f'node>{node_id}>provisioning>phase')
        recent_status = cortx_conf.get(f'node>{node_id}>provisioning>status')
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
                recent_status = cortx_conf.set(f'node>{node_id}>provisioning>status',
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

    @staticmethod
    def _load_consul_conf(_idx: str):
        """Load consul conf with given index if not already loaded."""
        #TODO: Remove  the function when gconf is moved to consul completely.
        with open(const.CONSUL_CONF_URL, 'r') as f:
            gconf_consul_url = f.read()
        try:
            Conf.load(_idx, gconf_consul_url)
        except ConfError:
            return 1
