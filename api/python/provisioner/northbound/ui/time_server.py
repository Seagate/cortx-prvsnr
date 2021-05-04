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
from provisioner import set_ntp
from ..data.data_store import PillarStore
from ..data.models import TimeServerModel


class TimeServerWindow(FormWindow):

    data = {
                'Time Server': {
                                   'default': 'time.seagate.com',
                                   'validation': 'hostname'
                               },
                'Time Zone': {
                                  'default': 'IST'
                             }
           }
    component_type = 'Time server'

    def action(self):
        content = {'_'.join(key.split(" ")): val['default']
                   for key, val in self.data.items()}
        time_server = TimeServerModel(**content)
        PillarStore().store_data(time_server)
        result = True
        err = None
        try:
            set_ntp(local=True)
        except Exception as exc:
            result = False
            err = str(exc)
        return result, err
