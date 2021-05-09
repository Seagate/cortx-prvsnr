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
    storage-set-1: 
  search_domains:                     # Do not update
  dns_servers:                        # Do not update
  server_nodes:
    - <machine_id_1>: srvnode-1
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
      mgmt:                           # Management network interfaces
        interfaces:
          - eth0
        public_ip:                    # DHCP is assumed if left blank
        netmask:
        gateway:                      # Gateway IP of Management Network. Not requried for DHCP.
      data:                           # Data network interfaces
        public_interfaces:
          - eth1                      # Public Data
        private_interfaces:
          - eth2                      # Private Data (direct connect)
        public_ip:                    # DHCP is assumed if left blank
        netmask:
        gateway:                      # Gateway IP of Public Data Network. Not requried for DHCP.
        private_ip: 192.168.0.1       # Fixed IP of Private Data Network
        roaming_ip: 192.168.0.3       # Applies to private data network
    storage:
      enclosure_id: enclosure-1
      metadata_devices:                # Device for /var/motr and possibly SWAP
        - /dev/sdb                    # Auto-populated by system.storage.multipath
      data_devices:                   # Data device/LUN from storage enclosure
        - /dev/sdc
