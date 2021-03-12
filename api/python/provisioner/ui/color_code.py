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
import config


class ColorCode:
    _instance = None

    def __init__(self):
        if self._instance:
            return self._instance
        else:
            curses.start_color()
            self._instance = self

    def create_color_pair(self, code, color1, color2):
        curses.init_pair(code, color1, color2)

    def get_color_pair(self, color_code):
        if not config.color_codes.get(color_code, None):
            raise Exception("No color code defined")
        return curses.color_pair(color_code)
