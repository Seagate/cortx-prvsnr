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
from window import Window
from color_code import ColorCode
from text_box import TextBox
from success import SuccessWindow


class HostnameWindow(Window):

    def create_window(self, **kwargs):
        color_code = kwargs['color_code']
        comp_name = ' '.join(kwargs['component'])

        self.create_menu_head()

        col_code_attr = ColorCode.get_color_pair(color_code)
        x = 3
        y = self.get_max_height() // 2 - 1
        self.on_attr(col_code_attr)
        self._window.addstr(y, x, f"Please enter {comp_name} for this machine")
        self.enable_keypad()
        self.off_attr(col_code_attr)
        data = TextBox(
                   self._window,
                   1,
                   16,
                   y+3,
                   x,
                   self.get_max_height()//4).create_textbox(color_code)

        self._window.clear()

        win = SuccessWindow(self._window)
        win.create_window(color_code=2,
                          data=f"{' '.join(self._parent)}:{data}")
