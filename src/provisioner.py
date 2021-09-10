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

from cortx.utils.process import SimpleProcess
from cortx.utils.conf_store import Conf


class ConfigStore:
  """ CORTX Config Store """

  @staticmethod
  def init(conf_url):
    CortxConfig._conf_url = conf_url
    CortxConfig._conf_idx = "cortx_conf"
    Conf.load(self._conf_idx, self._conf_url)

  @staticmethod
  def set_kvs(kvs: list):
    """ 
    Parameters:
    kvs - List of KV tuple, e.g. [('k1','v1'),('k2','v2')]
    """
    
    for key, val in kvs:
      Conf.set(self._conf_idx, key, val)
    Conf.save(self._conf_idx)

  @staticmethod
  def set(key: str, val: str):
    Conf.set(self._conf_idx, key, val)
    Conf.save(self._conf_idx)

  @staticmethod
  def get(key) -> str:
    """ Returns value for the given key """
    return Conf.get(self._conf_idx, key)


class CortxCluster:
  """ Represents CORTX Cluster """

  def __init___(node_list: list = []):
    """
    Creates cluster from the list of nodes.
    Each node in the is is a dict and contains following attributes
    - name: <name>
      id: <uniq id>
      storage_set: <storage_set_name>
      hostname: <fqdn>
      components:
      - name: <component 1>
        services:
        - <service name 1>
        - <service name 2>
      - name: <component 2>
        ...
      storage:
      - name: <cvg name>
        type: <cvg type>
        data_devices:
        - /dev/<device 1>
        - /dev/<device 2>
        metadata_devices:
        - /dev/<device 1>
        - /dev/<device 2>
    """
    self._node_list = node_list
    for node in node_list:
      self._validate(node)

  def _validate(self, node: dict):
    """ 
    validates a give node to habve required properties
    Raises exception if there is any entry missing
    """
    pass

  def _get_kvs(self) -> list:
    """ Returns list of keys and values representing cluster """
    pass  # TODO

  def add_node(self, node: dict):
    self._validate(node)
    self._node_list.append(node)

  def save(config_store):
    """ Saves cluster information onto the conf store """

    kvs = self._get_kvs()
    config_store.set_kvs(kvs)
    
         

class CortxProvisioner:
  """ CORTX Provosioner """

  _cortx_conf_url = "yaml:/etc/cortx/cluster.conf"

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

    Conf.load("solution_conf", solution_conf_url)

    if cortx_conf_url is not None:
      CortxProvisioner._cortx_conf_url = cortx_conf_url
    Conf.load("cortx_conf", CortxProvisioner._cortx_conf_url)

    # TODO: Read Cluster Conf and Construct Cluster to dump to Conf Store
    Conf.copy("solution_conf", "cortx_conf")

  @staticmethod
  def cluster_bootstrap(cortx_conf_url: str = None):
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
    Conf.load("cortx_config", cortx_conf_url)

    # TODO: Revert to the actual Conf Store format
    # Current this is readind using solution conf format
    node_types = Conf.get("cortx_config", "cluster>node_types")
    num_node_types = len(node_types)

    for i in range(0, num_node_types):
      components = Conf.get("cortx_config", f"cluster>node_types[{i}]>components")
      num_components = len(components)

      for j in range(0, num_components):
        services = Conf.get("cortx_config",
          f"cluster>node_types[{i}]>components[{j}]>services")
        service = 'all' if services is None else ','.join(services)
        print(f"{components[j]['name']}_setup --config {CortxProvisioner._cortx_conf_url} --services %s" %service)
        # TODO: Enable this code
        # rc, output = SimpleProcess(f"{components[i]}_setup --config \
        #  {CortxProvisioner._cortx_conf_url} --services %s" %services.join(","))
