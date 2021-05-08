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
#


key_mapping = {
                  'Hostname': {
                      'pillar_key': 'cluster/srvnode-0/hostname',
                      'confstore_key': 'hostname'
                  },
                  'Time_Server': {
                      'pillar_key': 'system/ntp/time_server',
                      'confstore_key': 'ntp>time_server'
                  },
                  'Time_Zone': {
                      'pillar_key': 'system/ntp/time_zone',
                      'confstore_key': 'ntp>time_zone'
                  },
                  'Ip_Mgmt': {
                      'pillar_key':
                          'cluster/srvnode-0/network/mgmt/public_ip',
                      'confstore_key':
                          'network>mgmt>public_ip'
                  },
                  'Gateway_Mgmt': {
                      'pillar_key': 'cluster/srvnode-0/network/mgmt/gateway',
                      'confstore_key': 'network>mgmt>gateway'
                  },
                  'Interfaces_Mgmt': {
                      'pillar_key':
                          'cluster/srvnode-0/network/mgmt/interfaces',
                      'confstore_key': 'network>mgmt>interfaces'
                  },
                  'Netmask_Mgmt': {
                      'pillar_key': 'cluster/srvnode-0/network/mgmt/netmask',
                      'confstore_key': 'network>mgmt>netmask'
                  },
                  'Management_VIP': {
                      'pillar_key': 'cluster/mgmt_vip',
                      'confstore_key': 'mgmt_vip'
                  }
              }
