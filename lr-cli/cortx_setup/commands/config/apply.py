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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

from provisioner.salt import cmd_run
# import socket
from cortx_setup.commands.command import Command
from cortx.utils.conf_store import Conf
from cortx_setup.config import (
    Stx_Cert_Path,
    FIREWALL_CONFIG_PATH
)
from cortx_setup.commands.server.config import (
    ServerConfig
)
from cortx_setup.commands.network.config import (
    NetworkConfig
)
from cortx_setup.commands.storage.config import (
    StorageEnclosureConfig
)
from cortx_setup.commands.security.config import (
    SecurityConfig
)
from cortx_setup.commands.node.initialize import(
    NodeInitialize
)
from cortx_setup.commands.node.prepare.network import(
    NodePrepareNetwork
)
from cortx_setup.commands.node.prepare.time import(
    NodePrepareTime
)
from cortx_setup.commands.node.prepare.finalize import(
    NodePrepareFinalize
)
from cortx_setup.commands.node.prepare.config import(
    NodePrepareServerConfig
)
from cortx_setup.commands.confstore import(
    PrepareConfstore
)
from provisioner.commands import PillarSet

class CortxConfigApply(Command):
    _args = {
        'file': {
            'type': str,
            'optional': True
        }
    }

    def run(self, **kwargs):
        try:
            index = 'config_apply_index'
            self.logger.debug("loading Solution config")
            Solution_template_path = kwargs.get('file')
            try:
                self.load_conf_store(index, Solution_template_path)
            except Exception:
                self.logger.debug("index already present, using the same")

            #Below logic can be used in future in case of Multi-node solution-config file.
            # local_fqdn= socket.gethostbyname()
            # server_nodes= Conf.get(index,'cluster>storage_sets>server_nodes')
            # for node in enumerate(server_nodes):
            #     if Conf.get(index,f'{server_nodes[node]}>hostname') is == local_fqdn:
            #         ARG_server_nodes= server_nodes[node]


            self.logger.debug("Loading Default Confstore Values for cortx")
            PrepareConfstore().run()

            self.logger.info("Applying server configuration")
            ARG_Server_Name = Conf.get(index,'cluster>storage_sets>server_nodes')
            Server_Name= ARG_Server_Name[0]
            ARG_Server_Type= Conf.get(index,f'{Server_Name}>type')
            server_args= {'name':ARG_Server_Name[0],'type':ARG_Server_Type}
            ServerConfig().run(**server_args)

            self.logger.info("Applying network configuration")
            ARG_Network_Transport= 'lnet'
            ARG_Network_mode= 'tcp'
            network_mode_args= {'transport':ARG_Network_Transport,'mode':ARG_Network_mode}
            NetworkConfig().run(**network_mode_args)

            ARG_Mgmt_Interface= Conf.get(index,f'{Server_Name}>network>management>interfaces')
            mgmt_interface_args={'interfaces':ARG_Mgmt_Interface,'network_type':'management'}
            NetworkConfig().run(**mgmt_interface_args)

            ARG_Data_Interface= Conf.get(index,f'{Server_Name}>network>data>interfaces')
            data_interface_args={'interfaces':ARG_Data_Interface,'network_type':'data'}
            NetworkConfig().run(**data_interface_args)

            ARG_Private_Interface= Conf.get(index,f'{Server_Name}>network>private>interfaces')
            private_interface_args={'interfaces':ARG_Private_Interface,'network_type':'private'}
            NetworkConfig().run(**private_interface_args)

            BMC_Info= Conf.get(index,f'{Server_Name}>bmc')
            if BMC_Info is not None :
                self.logger.info("Applying BMC configuration")
                ARG_Bmc_Ip= Conf.get(index,f'{Server_Name}>bmc>ip')
                ARG_Bmc_Username= Conf.get(index,f'{Server_Name}>bmc>username')
                ARG_Bmc_Password= Conf.get(index,f'{Server_Name}>bmc>password')
                bmc_args={'bmc':ARG_Bmc_Ip,'user':ARG_Bmc_Username,'password':ARG_Bmc_Password}
                NetworkConfig().run(**bmc_args)

            Storage_Enclosure_Name= Conf.get(index,f'{Server_Name}>storage>enclosure')
            Storage_Info= Conf.get(index,f'{Storage_Enclosure_Name}')
            if Storage_Info is not None :
                self.logger.info("Applying Storage configuration")
                ARG_Primary_Ip= Conf.get(index,f'{Storage_Enclosure_Name}>controller>primary>ip')
                ARG_Primary_Port= Conf.get(index,f'{Storage_Enclosure_Name}>controller>primary>port')
                ARG_Secondary_Ip= Conf.get(index,f'{Storage_Enclosure_Name}>controller>secondary>ip')
                ARG_Secondary_Port= Conf.get(index,f'{Storage_Enclosure_Name}>controller>secondary>port')
                ARG_Controller_User= Conf.get(index,f'{Storage_Enclosure_Name}>controller>username')
                ARG_Controller_Password= Conf.get(index,f'{Storage_Enclosure_Name}>controller>password')
                storage_primary_args={'mode':'primary','ip':ARG_Primary_Ip,'port':ARG_Primary_Port,'user':ARG_Controller_User,'password':ARG_Controller_Password}
                StorageEnclosureConfig().run(**storage_primary_args)

                storage_secondary_args={'mode':'secondary','ip':ARG_Secondary_Ip,'port':ARG_Secondary_Port,'user':ARG_Controller_User,'password':ARG_Controller_Password}
                StorageEnclosureConfig().run(**storage_secondary_args)

                ARG_Enclosure_Name= Conf.get(index,f'{Storage_Enclosure_Name}>name')
                ARG_Controller_Type= Conf.get(index,f'{Storage_Enclosure_Name}>controller>type')
                ARG_Storage_Type= Conf.get(index,f'{Storage_Enclosure_Name}>type')
                controller_args= {'controller':ARG_Controller_Type,'name':ARG_Enclosure_Name,'type':ARG_Storage_Type}
                StorageEnclosureConfig().run(**controller_args)

            ARG_Cvg_Devices= Conf.get(index,f'{Server_Name}>storage>cvg')
            for cvg_count,cvg_data in enumerate(ARG_Cvg_Devices):
                self.logger.debug(f"storing cvg devices data in confstore: {cvg_data}")
                cvg_args={'cvg': ARG_Cvg_Devices[cvg_count]['name'],'data_devices': ARG_Cvg_Devices[cvg_count]['data_devices'],'metadata_devices': ARG_Cvg_Devices[cvg_count]['metadata_devices']}
                StorageEnclosureConfig().run(**cvg_args)
            self.logger.info("Updating Certs")
            certs={'certificate':Stx_Cert_Path}
            SecurityConfig().run(**certs)

            self.logger.debug("Calling Components Post Install configuration")
            if Conf.get(index, 'cortx>software>common>product_release') == 'LC':
                ARG_COMPONENTS= Conf.get(index,'cortx>software>services')
                comp_maping = {'utils': 'cortx_utils', 's3': 's3server'}
                category = {'cortx_utils': 'foundation', 'motr': 'iopath', 'hare': 'iopath', 's3server': 'iopath', 'csm': 'controlpath','sspl':'controlpath','uds':'controlpath','ha':'ha'}
                all_components = {'foundation': [], 'iopath': [], 'controlpath': []}
                for component in ARG_COMPONENTS:
                    component = comp_maping.get(component) if comp_maping.get(component, None) else component
                    all_components[category.get(component)].append(component)
                for component_category, services in all_components.items():
                    PillarSet().run(
                        f'execution/cortx_components/{component_category}',
                                services,
                                local=True
                    )

            NodeInitialize().run()


            self.logger.info("Configuring Network Interfaces")
            ARG_Site_Id='1'
            ARG_Rack_Id='1'
            ARG_Node_Id=Server_Name[-1]
            server_config_args={'site_id':ARG_Site_Id,'rack_id':ARG_Rack_Id,'node_id':ARG_Node_Id}
            NodePrepareServerConfig().run(**server_config_args)

            ARG_Network_Hostname= Conf.get(index,f'{Server_Name}>hostname')
            ARG_Dns_Servers= Conf.get(index,'cluster>network>management>dns_servers')
            ARG_Search_Domains= Conf.get(index,'cluster>network>management>search_domains')
            hostname_args= {'hostname':ARG_Network_Hostname,'dns_servers':ARG_Dns_Servers,'search_domains':ARG_Search_Domains}
            NodePrepareNetwork().run(**hostname_args)

            ARG_Mgmt_Ip= Conf.get(index,f'{Server_Name}>network>management>ipaddress')
            ARG_Mgmt_Netmask= Conf.get(index,f'{Server_Name}>network>management>netmask')
            ARG_Mgmt_Gateway= Conf.get(index,f'{Server_Name}>network>management>gateway')
            mgmt_network_args= {'network_type':'managment','ip_address':ARG_Mgmt_Ip,'netmask':ARG_Mgmt_Netmask,'gateway':ARG_Mgmt_Gateway}
            NodePrepareNetwork().run(**mgmt_network_args)

            ARG_Data_Ip= Conf.get(index,f'{Server_Name}>network>data>ipaddress')
            ARG_Data_Netmask= Conf.get(index,f'{Server_Name}>network>data>netmask')
            ARG_Data_Gateway= Conf.get(index,f'{Server_Name}>network>data>gateway')
            data_network_args= {'network_type':'data','ip_address':ARG_Data_Ip,'netmask':ARG_Data_Netmask,'gateway':ARG_Data_Gateway}
            NodePrepareNetwork().run(**data_network_args)

            ARG_Private_Ip= Conf.get(index,f'{Server_Name}>network>private>ipaddress')
            ARG_Private_Netmask= Conf.get(index,f'{Server_Name}>network>private>netmask')
            ARG_Private_Gateway= Conf.get(index,f'{Server_Name}>network>private>gateway')
            private_network_args= {'network_type':'private','ip_address':ARG_Private_Ip,'netmask':ARG_Private_Netmask,'gateway':ARG_Private_Gateway}
            NodePrepareNetwork().run(**private_network_args)

            self.logger.info("Applying Firewall configuration")
            cmd_run(f'cortx_setup node prepare firewall --config {FIREWALL_CONFIG_PATH}')

            self.logger.info("Applying NTP configuration")
            Ntp_Timezone_args= {'server':'time.seagate.com','timezone':'UTC'}
            NodePrepareTime().run(**Ntp_Timezone_args)

            self.logger.info("Finalize Node Prepareation")
            NodePrepareFinalize().run()
        except Exception as ex:
            raise ex
        self.logger.info("Done")
