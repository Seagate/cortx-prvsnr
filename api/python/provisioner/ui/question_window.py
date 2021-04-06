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
from .window import Window
from .color_code import ColorCode


class QuestionWindow(Window):
    _menu = ["Yes", "No"]
    _question = "Is this ?"

    def get_menu(self):
        return self._menu

    def create_window(self, **kwargs):

        color_code = kwargs['color_code']
        if 'selected' not in kwargs:
            selected = "Yes"
        else:
            selected = kwargs['selected']

        self.create_menu_head()
        self._window.border()
        col_code_attr = ColorCode.get_color_pair(color_code)
        x = 3
        y = self.get_max_height() // 2 - 1
        self._window.addstr(y, x, f"{self._question}")
        if selected == "Yes":
            self.on_attr(col_code_attr)
            self._window.addstr(y+2, x, f">> Yes")
            self.off_attr(col_code_attr)
            self._window.addstr(y+4, x+3, f"No")
        else:
            self.on_attr(col_code_attr)
            self._window.addstr(y+4, x, f">> No")
            self.off_attr(col_code_attr)
            self._window.addstr(y+2, x+3, f"Yes")

        self._window.refresh()

    def process_input(self, color_code):
        current_row = 0
        while 1:
            key = self._window.getch()
            self._window.clear()
            if key == curses.KEY_UP and current_row > 0:
                current_row = current_row - 1
            elif (key == curses.KEY_DOWN and
                  current_row < len(self.get_menu()) - 1):
                current_row = current_row + 1
            elif key == curses.KEY_ENTER or key in (10, 13):
                if current_row == 0:
                    self.yes_action()
                    current_row = 0
                    break
                else:
                    self.no_action()
                    current_row = 0
                    break

            self._window.clear()
            self.create_window(color_code=color_code,
                               selected=self._menu[current_row])
            self._window.refresh()

    def no_action(self):
        pass

    def yes_action(self):
        pass
