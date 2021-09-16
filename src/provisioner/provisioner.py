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

# TODO: Uncomment when mini provisioners are enabled
# from cortx.utils.process import SimpleProcess
from cortx.utils.conf_store import Conf
from cortx.provisioner.config_store import ConfigStore
from cortx.provisioner.cluster import CortxCluster


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
        # TODO: To convert CORTX config
        cortx_config_store.set('cortx', Conf.get(CortxProvisioner._solution_index, 'cortx'))

    @staticmethod
    def config_apply_cluster(cortx_config_store):
        node_map = {}
        node_types = Conf.get(CortxProvisioner._solution_index, 'cluster>node_types')
        for node_type in node_types:
            node_map[node_type['name']] = node_type

        storage_sets = Conf.get(CortxProvisioner._solution_index, 'cluster>storage_sets')
        nodes = []
        for storage_set in storage_sets:
            for node in storage_set['nodes']:
                node_type = node['type']
                node = dict(node_map[node_type], **node)
                node['storage_set'] = storage_set['name']
                nodes.append(node)

        cs = CortxCluster(nodes)
        cs.save(cortx_config_store)

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
        num_components = len(components)
        mp_interfaces = ['post_install', 'prepare', 'config', 'init']
        for interface in mp_interfaces:
            for j in range(0, num_components):
                services = cortx_config_store.get(
                    f'node>{node_id}>components[{j}]>services')
                service = 'all' if services is None else ','.join(services)
                print(f"{components[j]['name']}_setup --config \
                    {CortxProvisioner._cortx_conf_url} {interface} --services \
                    %s" % service)

                # TODO: Enable this code
                rc, output = SimpleProcess(f"{components[j]['name']}_setup \
                    --config {CortxProvisioner._cortx_conf_url} {interface} \
                    --services %s" % service)