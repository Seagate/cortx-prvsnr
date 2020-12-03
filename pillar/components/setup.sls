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

setup:
  config:
    master: []      # list of salt masters to set (for backward compatibility)
  factory: {}       # factory setup arguments
  connections:
    # order of connection resolving:
    #  - value for the specific service (e.g. 'connections:ssh:host')
    #  - default value in 'connections:default'
    #  - 'cluster:<grains.id>:network:data_nw:pvt_ip_addr'
    default:        # IP/domain endpoint that specifies default destinations
                    # for incoming connections for the services listed below
    ssh:
      host:         # destination endpoint for incoming ssh client connections
      port: 22
      user: root
    glusterfs:
      peer:         # destination endpoint for incoming peering requests
    saltstack:
      master:       # destination endpoint for incoming salt-minion connections
