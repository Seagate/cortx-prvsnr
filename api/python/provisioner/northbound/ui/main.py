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
from .main_menu import MainMenu
from .color_code import ColorCode
from .header import HeaderWindow
from .window import Window


def main(stdscr):
    curses.initscr()
    curses.curs_set(0)
    ColorCode()

    wind = Window(stdscr)
    # Divide screen into 2 parts
    # Header window 1 / 5 th of actual size of window
    # starting from point(1, 1) to (max_height/5, max_width-1)
    config.header_height = wind._max_h // 5
    header_window = curses.newwin(wind._max_h // 5, wind._max_w - 1, 1, 1)
    HeaderWindow(header_window).create_window(color_code=config.menu_color)

    # Main window 4 / 5 th of actual size of window
    # starting from point(max_height/5, 1) to (max_height , max_width-1)
    main_window = curses.newwin(
                      wind._max_h - wind._max_h // 5,
                      wind._max_w - 1,
                      wind._max_h // 5,
                      1
                  )

    winds = MainMenu(main_window)
    winds.enable_keypad()
    winds.create_window(color_code=config.menu_color, menu_code=0)
    winds.process_input(config.menu_color)


def start_tui():
    curses.wrapper(main)


if __name__ == '__main__':
    start_tui()
