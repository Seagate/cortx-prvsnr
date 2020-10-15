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

import logging
from os import path
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class ClusterInfo():
    def __init__(self):
        """Read cluster info and store it"""
        self.cluster_info = self.__read_cluster_sls()

    @staticmethod
    def get_cluster_sls_path():
        # uu_cluster_sls_paths = [
        #     "/var/lib/seagate/cortx/provisioner/shared/srv/pillar/groups/all/uu_cluster.sls",
        #     "/srv/glusterfs/volume_prvsnr_data/srv/pillar/groups/all/uu_cluster.sls"
        # ]
        # cluster_sls_path = None

        # for cl_sls_path in uu_cluster_sls_paths:
        #     if path.isfile(cl_sls_path):
        #         cluster_sls_path = cl_sls_path
        #         break

        # if not cluster_sls_path:
        #     err_msg = "Error: Cluster data is not updated correctly"
        #     logger.error(err_msg)
        #     raise Exception(err_msg)

        cluster_sls_path = '/opt/seagate/cortx/provisioner/pillar/components/cluster.sls'
        return cluster_sls_path

    def __read_cluster_sls(self):
        file_path = self.get_cluster_sls_path()
        logger.info(f"Reading cluster info from {file_path}")
        yaml_file = Path(file_path)
        # Read the cluster.sls into a dict object
        yaml_dict = yaml.safe_load(yaml_file.read_text())
        if 'cluster' not in yaml_dict:
            logger.error("Invalid data in cluster.sls")
            return None
        return yaml_dict['cluster']

    def __is_valid_node(self, node):
        if node not in self.cluster_info['node_list']:
            logger.error(f"Invaid node: '{node}'")
            return False
        return True


    def get_nodes(self):
        """This function returns the node list"""
        logger.info("Getting nodes from cluster.sls")
        node_list = self.cluster_info['node_list']
        logger.info(node_list)
        return node_list

    def get_data_nw(self, node):
        """This function returns the data network details"""
        logger.info(f"Read data network for '{node}'")
        data_nw = None
        if self.__is_valid_node(node):
            data_nw = self.cluster_info[node]['network']['data_nw']
            logger.info(f"Data network : {data_nw}")
        return data_nw

    def get_pvt_ip_addr(self, node):
        """This function returns the private ip address for the node"""
        logger.debug(f"Read private ip address for '{node}'")
        pvt_ip_addr = None
        if self.__is_valid_node(node):
            pvt_ip_addr = self.cluster_info[node]['network']['data_nw']['pvt_ip_addr']
            logger.info(pvt_ip_addr)
        return pvt_ip_addr

    def get_pub_data_iface(self, node):
        """This function returns the public data interface for the node"""
        logger.debug(f"Read public data iface for '{node}'")
        pub_iface = None
        if self.__is_valid_node(node):
            pub_iface = self.cluster_info[node]['network']['data_nw']['iface']
            logger.info(pub_iface)
        return pub_iface

