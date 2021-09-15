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
# TODO: Uncomment when mini provisioners are enabled
# from cortx.utils.process import SimpleProcess
from cortx.utils.conf_store import Conf
from cortx.provisioner.error import CortxProvisionerError
from cortx.provisioner.config_store import ConfigStore
from cortx.provisioner.config import CortxConfig
from cortx.provisioner.cluster import CortxCluster,  CortxStorageSet


class CortxProvisioner:
    """ CORTX Provosioner """

    _cortx_conf_url = "yaml:///etc/cortx/cluster.conf"
    _solution_index = "solution_conf"

    @staticmethod
    def init():
        pass

    @staticmethod
    def config_apply(solution_conf_url: str, cortx_conf_url: str = None):
        """
        Description:
        Parses input config and store in CORTX config location

        Parameters:
        [IN]  Solution Config URL
        [OUT] CORTX Config URL
        """

        Conf.load(CortxProvisioner._solution_index, solution_conf_url)

        if cortx_conf_url is None:
            cortx_conf_url = CortxProvisioner._cortx_conf_url
        cortx_config_store = ConfigStore(cortx_conf_url)

        if Conf.get(CortxProvisioner._solution_index, 'cluster') is not None:
            CortxProvisioner.config_apply_cluster(cortx_config_store)

        if Conf.get(CortxProvisioner._solution_index, 'cortx') is not None:
            CortxProvisioner.config_apply_cortx(cortx_config_store)


    @staticmethod
    def config_apply_cortx(cortx_config_store):
        """ Convert CORTX config into confstore keys """
        cortx_config = Conf.get(CortxProvisioner._solution_index, 'cortx')
        cs = CortxConfig(cortx_config)
        cs.save(cortx_config_store)

    @staticmethod
    def config_apply_cluster(cortx_config_store):
        node_map = {}
        try:
            node_types = Conf.get(CortxProvisioner._solution_index, 'cluster>node_types')
            for node_type in node_types:
                node_map[node_type['name']] = node_type

            cluster_id = Conf.get(CortxProvisioner._solution_index, "cluster>id")
            if cluster_id is None:
                raise CortxProvisionerError(
                    errno.EINVAL,
                    f'cluster_id property is unspecified for cluster.')

            cluster_name = Conf.get(CortxProvisioner._solution_index, "cluster>name")
            if cluster_name is None:
                raise CortxProvisionerError(
                    errno.EINVAL,
                    f'cluster_name property is unspecified for cluster.')
            cluster_keys = [("id", cluster_id), ("name", cluster_name)]
            cortx_config_store.set('cluster', cluster_keys)

            storage_sets = Conf.get(CortxProvisioner._solution_index, 'cluster>storage_sets')
            if storage_sets is None:
                raise CortxProvisionerError(
                    errno.EINVAL,
                    f'storage_sets property is unspecified for cluster.')

            nodes = []
            for storage_set in storage_sets:
                for node in storage_set['nodes']:
                    node_type = node['type']
                    node = dict(node_map[node_type], **node)
                    node['storage_set'] = storage_set['name']
                    node['storage_set_count'] = len(storage_sets)
                    node['cluster_id'] = cluster_id
                    nodes.append(node)

            cs = CortxCluster(nodes)
            cs.save(cortx_config_store)
            cs = CortxStorageSet(storage_sets)
            cs.save(cortx_config_store)
        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while applying cluster_config {e}')

    @staticmethod
    def cluster_bootstrap(node_id: str, cortx_conf_url: str = None):
        """
        Description:
        Configures Cluster Components
        1. Reads Cortx Config and obtain cluster components
        2. Invoke Mini Provisioners of cluster components

        Paramaters:
        [IN] CORTX Config URL
        """

        if cortx_conf_url is None:
            cortx_conf_url = CortxProvisioner._cortx_conf_url
        cortx_config_store = ConfigStore(cortx_conf_url)

        components = cortx_config_store.get(f'node>{node_id}>components')
        for comp_name in components.keys():
            services = cortx_config_store.get(f'node>{node_id}>components>{comp_name}>services')
            service = 'all' if services is None else ','.join(services)
            print(f"{comp_name}_setup --config {CortxProvisioner._cortx_conf_url} --services %s" % service)

            # TODO: Enable this code
            # rc, output = SimpleProcess(f"{components[i]}_setup --config \
            #  {CortxProvisioner._cortx_conf_url} --services %s" %services.join(","))
