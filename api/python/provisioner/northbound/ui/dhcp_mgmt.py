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
from .form_window import FormWindow
from provisioner.northbound.data.models import MgmtNetworkModel
from ..data.data_store import PillarStore
from provisioner import set_mgmt_network


class DhcpMGMTNetworkWindow(FormWindow):

    data = {
            'Interfaces Mgmt': {
                      'default': 'eth0'
                  }
           }
    component_type = 'Management Network'

    def action(self):
        content = {'_'.join(key.split(" ")): val['default']
                   for key, val in self.data.items()}
        content['Ip_Mgmt'] = None
        content['Gateway_Mgmt'] = None
        content['Netmask_Mgmt'] = None

        mgmt_network = MgmtNetworkModel(**content)
        PillarStore().store_data(mgmt_network)
        result = True
        err = None
        try:
            set_mgmt_network(local=True)
        except Exception as exc:
            result = False
            err = str(exc)
        return result, err
