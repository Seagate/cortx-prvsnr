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
from window import Window
from color_code import ColorCode


class MainMenu(Window):
    _menu = None

    def __init__(self, window):
        super().__init__(window)
        self._menu = config.menu

    def get_menu(self):
        return self._menu

    def create_window(self, **kwargs):
        color_code = kwargs['color_code']
        selected_rows = kwargs['menu_code']
        col_code_attr = ColorCode.get_color_pair(color_code)
        for idx, row in enumerate(self._menu):
            x = self.get_max_width() // 2 - len(row)//2
            y = self.get_max_height() // 2 - len(self._menu)//2 + idx
            if idx == selected_rows:
                self.on_attr(col_code_attr)
                self._window.addstr(y, x-3, ">> ")
                self._window.addstr(y, x, row)
                self.off_attr(col_code_attr)
            else:
                self._window.addstr(y, x, row)
        self._window.refresh()

    def process_input(self, color_code):
        current_row = 0
        while 1:
            key = self._window.getch()
            self._window.clear()

            if key == curses.KEY_UP and current_row > 0:
                current_row = current_row - 1
            elif (
                key == curses.KEY_DOWN and
                current_row < len(self.get_menu()) - 1
            ):
                current_row = current_row + 1
            elif key == 113:
                return
            elif key == curses.KEY_ENTER or key in (10, 13):
                if current_row == len(self.get_menu()) - 1:
                    return

            self._window.clear()
            self.create_default_window(config.default_window_color)
            self.create_window(color_code=color_code, menu_code=current_row)
            self._window.refresh()
