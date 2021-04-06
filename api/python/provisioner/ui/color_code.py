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
import curses
from . import config
from provisioner.errors import ProvisionerError


class ColorCode:
    _color_codes = None

    def __init__(self):
        curses.start_color()
        self._color_codes = config.color_codes
        self.create_color_pair()

    def create_color_pair(self):
        for code, color in self._color_codes.items():
            curses.init_pair(code, color[0], color[1])

    @staticmethod
    def get_color_pair(color_code):
        if not config.color_codes.get(color_code, None):
            raise ProvisionerError(f"Color code {color_code} not defined")
        return curses.color_pair(color_code)
