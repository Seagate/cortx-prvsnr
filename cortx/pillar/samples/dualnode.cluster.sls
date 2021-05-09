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

cluster:
  cluster_id:
  storage_sets:
    storage_set_1:
      - srvnode-1
      - srvnode-2
  search_domains:                     # Do not update
  dns_servers:                        # Do not update
  server_nodes:
    - <machine_id_1>: srvnode-1
    - <machine_id_2>: srvnode-2
  srvnode-1:
    rack_id:
    site_id:
    storage_set_id:
    node_id:
    machine_id:
    hostname: srvnode-1
    is_primary: true
    roles:
      - primary
      - openldap_server
    bmc:
      ip:
      user: ADMIN
      secret:
    network:
      mgmt:                         # Management network interfaces
        interfaces:
          - eno1
        public_ip:                  # DHCP is assumed if left blank
        netmask:
        gateway:                    # Gateway IP of Management Network. Not requried for DHCP.
      data:                         # Data network interfaces
        public_interfaces:
          - enp175s0f0              # Public Data
        private_interfaces:
          - enp175s0f1              # Private Data (direct connect)
        public_ip:                  # DHCP is assumed if left blank
        netmask:
        gateway:                    # Gateway IP of Public Data Network. Not requried for DHCP.
        private_ip: 192.168.0.1     # Fixed IP of Private Data Network
        roaming_ip: 192.168.0.3     # Applies to private data network
    storage:
      enclosure_id: enclosure-1 
      metadata_devices:             # Device for /var/motr and possibly SWAP
        - /dev/sdb                  # Auto-populated by system.storage.multipath
      data_devices:                 # Data device/LUN from storage enclosure
        - /dev/sdc                  # Auto-populated by system.storage.multipath
  srvnode-2:
    hostname: srvnode-2
    rack_id:
    site_id:
    storage_set_id:
    node_id:
    machine_id:
    is_primary: false
    bmc:
      ip:
      user: ADMIN
      secret:
    network:
      mgmt:                         # Management network interfaces
        interfaces:
          - eno1
        public_ip:                  # DHCP is assumed if left blank
        netmask:
        gateway:                    # Gateway IP of Management Network. Not requried for DHCP.
      data:                         # Data network interfaces
        public_interfaces:
          - enp175s0f0              # Public Data
        private_interfaces:
          - enp175s0f1              # Private Data (direct connect)
        public_ip:                  # DHCP is assumed, if left blank
        netmask:
        gateway:                    # Gateway IP of Public Data Network. Not requried for DHCP.
        private_ip: 192.168.0.2     # Fixed IP of Private Data Network
        roaming_ip: 192.168.0.4     # Applies to private data network
    storage:
      enclosure_id: enclosure-2
      metadata_devices:             # Device for /var/motr and possibly SWAP
        - /dev/sdb
      data_devices:                 # Data device/LUN from storage enclosure
        - /dev/sdc
  replace_node:
    minion_id: null                 # Could be srvnode-1, srvnode-2 or something similar
