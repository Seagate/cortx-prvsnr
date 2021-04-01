#!/usr/bin/env python
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
#
from form_window import FormWindow


class StaticBMCNetworkWindow(FormWindow):

    data = {
            'Ip': {
                      'default': '10.10.10.11',
                      'validation': 'ipv4',
                      'pillar_key': 'srvnode-0/bmc/ip'
                  },
            'Netmask': {
                           'default': '1.255.255.251',
                           'validation': 'ipv4',
                           'pillar_key': 'srvnode-0/bmc/netmask'
                       },
            'Gateway': {
                           'default': '198.162.0.1',
                           'validation': 'ipv4',
                           'pillar_key': 'srvnode-0/bmc/gateway'
                       }
           }
    component_type = 'BMC Network'
