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
from main_menu import MainMenu
from color_code import ColorCode


def main(stdscr):
    curses.initscr()
    curses.curs_set(0)
    ColorCode.init()
    for code, color in config.color_codes.items():
        ColorCode.create_color_pair(code, color[0], color[1])
    wind = MainMenu(stdscr)
    wind.create_default_window(config.default_window_color)
    wind.create_window(color_code=config.menu_color, menu_code=0)
    wind.process_input(config.menu_color)


if __name__ == '__main__':
    curses.wrapper(main)
