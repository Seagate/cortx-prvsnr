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
from curses.textpad import Textbox


class TextBox():
    _text = None
    _window = None

    def __init__(self, window, h, w, y, x, header_height):
        self.h = h
        self.w = w
        self.x = x
        self.y = y
        self.header_height = header_height
        self._window = window

    def create_textbox(self, color_code, default_value=None):
        is_valid = False

        while(not is_valid):
            self._window.hline(self.y + 1, self.x, "_", 16)
            self._window.refresh()

            new_win = curses.newwin(self.h, self.w,
                                    self.y + self.header_height, self.x)
            text = Textbox(new_win, insert_mode=False)

            if default_value:
                for i in default_value:
                    text.do_command(ord(i))

            return text.edit()
