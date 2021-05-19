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
import importlib
from .window import Window
from .color_code import ColorCode


class MainMenu(Window):
    _menu = None
    _menu_dict = None

    def __init__(self, window):
        super().__init__(window)
        self.set_menus(config.menu)
        self._menu_dict = config.menu
        self._menu.append("Exit")

    def get_menu(self):
        return self._menu

    def set_menus(self, menu):
        self._menu_dict = menu
        tmp_menu = list(menu.keys())
        self._menu = tmp_menu

    def create_window(self, **kwargs):
        color_code = kwargs['color_code']
        selected_rows = kwargs['menu_code']
        self._window.border()
        col_code_attr = ColorCode.get_color_pair(color_code)
        self.create_menu_head()

        for idx, row in enumerate(self._menu):
            # to display menu at the middle of screen
            x = self.get_max_width() // 2 - len(row) // 2
            y = self.get_max_height() // 2 - len(self._menu) // 2 + idx

            if idx == selected_rows:
                # Selected row should be start with >> for
                # better visual effects
                row_curser = ">> "
                self.on_attr(col_code_attr)
                self._window.addstr(y, x - len(row_curser), row_curser)
                self._window.addstr(y, x, row)
                self.off_attr(col_code_attr)
            else:
                self._window.addstr(y, x, row)

        self._window.refresh()

    def previos_menu(self):
        self._parent.pop()
        if self._parent == []:
            ext_menu = "Exit"
        else:
            ext_menu = "Back"
        menu = config.menu

        for level in self._parent:
            menu = menu[level]

        self.set_menus(menu)
        self._menu.append(ext_menu)

    def process_input(self, color_code):  # noqa: C901
        current_row = 0
        while 1:
            key = self._window.getch()
            self._window.clear()
            # go up in menu list
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            # go down in menu list
            elif (
                key == curses.KEY_DOWN and
                current_row < len(self.get_menu()) - 1
            ):
                current_row += 1
            # Select menu option from list
            elif key == curses.KEY_ENTER or key in (config.Key.EXIT_1.value,
                                                    config.Key.EXIT_2.value):

                # condition for Back button
                if current_row == len(self.get_menu()) - 1:

                    if self._parent == []:
                        return

                    self.previos_menu()

                # condition for Main menu
                elif current_row >= 0 and current_row < len(self.get_menu()):
                    key = self._menu[current_row]

                    # Nested menu condition
                    if isinstance(self._menu_dict[key], dict):
                        self._parent.append(key)
                        self.set_menus(self._menu_dict[key])
                        self._menu.append("Back")
                        current_row = 0
                    else:
                        self._parent.append(key)
                        module, cls = self._menu_dict[key].split(":")

                        try:
                            wid_mod = importlib.import_module(
                                f'.{module}', 'provisioner.ui'
                            )
                        except ImportError:
                            raise

                        # Load/Open window for given Menu
                        Pm_w = getattr(wid_mod, cls)
                        wd = Pm_w(self._window)
                        wd._parent = self._parent
                        wd.create_window(
                            color_code=color_code,
                            component=self._parent
                        )

                        if hasattr(wd, 'process_input'):
                            wd.process_input(
                                 color_code=color_code)
                        self._parent.remove(key)

            self._window.clear()
            self.create_window(color_code=color_code, menu_code=current_row)
            self._window.refresh()
