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
from . import config
from .color_code import ColorCode


class Window:
    _max_h = None
    _max_w = None
    _window = None
    _parent = []

    def __init__(self, window):
        self._max_h, self._max_w = window.getmaxyx()
        self._window = window
        self._window.border()

    def enable_keypad(self):
        self._window.keypad(1)

    def get_max_height(self):
        return self._max_h

    def get_max_width(self):
        return self._max_w

    def on_attr(self, attr):
        self._window.attron(attr)

    def off_attr(self, attr):
        self._window.attroff(attr)

    def create_menu_head(self):
        menu_header = '>> '.join(self._parent)
        if menu_header:
            menu_header = menu_header + ":"
        col_code_attr = ColorCode.get_color_pair(config.default_menu_head)
        self.on_attr(col_code_attr)
        self._window.addstr(2, 4, menu_header)
        self.off_attr(col_code_attr)

    def create_window(self, **kwargs):
        pass
