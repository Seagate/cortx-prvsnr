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
from .window import Window
from .color_code import ColorCode
from .text_box import TextBox
from .success import SuccessWindow
from .pillar import Pillar


class FormWindow(Window):

    data = {
               'Ip': {
                         'default': '127.0.0.1',
                         'validation': 'ipv4',
                         'pillar_key': 'srvnode-0/ip'
                     }
           }
    component_type = 'Default User input'

    def update_pillar(self):
        result = True
        for key in self.data.keys():
            if self.data[key]['pillar_key']:
                if (not Pillar.set_pillar(self.data[key]['pillar_key'],
                                          self.data[key]['default'])):
                    result = False
        return result

    def format_data(self):
        result = ''
        for key in self.data.keys():
            result = result + f"{key}: {self.data[key]['default']} "
        return result

    def submit_button(self, x, y, menu, selected_rows):
        buttons = {
           "Submit": x + 15,
           "Cancel": x + 5
        }
        selected_button = None

        if selected_rows == len(menu):
            selected_button = "Submit"
        elif selected_rows == len(menu) + 1:
            selected_button = "Cancel"

        for button in buttons.keys():
            if selected_button == button:
                cod = ColorCode.get_color_pair(1)
                self.on_attr(cod)
                self._window.addstr(y + 1, buttons[button], button)
                self.off_attr(cod)
            else:
                self._window.addstr(y + 1, buttons[button], button)

    @staticmethod
    def parse_input(kwargs):
        if 'selected' not in kwargs:
            selected_rows = 0
        else:
            selected_rows = kwargs['selected']

        if 'edit' not in kwargs:
            edit = False
        else:
            edit = kwargs['edit']
        return selected_rows, edit

    def action(self):
        pass

    def create_window(self, **kwargs):
        color_code = kwargs['color_code']
        self._parent = kwargs['component']

        selected_rows, edit = FormWindow.parse_input(kwargs)
        self._window.border()
        col_code_attr = ColorCode.get_color_pair(color_code)
        self.create_menu_head()

        screen_y_height = self.get_max_height() // 3
        # left margin for form heading
        x = 3
        # height for form heading
        y = screen_y_height - 2
        self.enable_keypad()

        self.on_attr(col_code_attr)
        # form heading
        self._window.addstr(y, x, f"Please enter {self.component_type}"
                            " for this machine")
        self.off_attr(col_code_attr)

        values = list(self.data.keys())
        # list all form content
        count_m = len(values)
        mid_count_m = count_m // 2

        # left margin for any label
        x_label = 6
        # left margin for any values
        x_values = x_label + 20

        # Display form
        for idx, row in enumerate(values):
            y = screen_y_height - mid_count_m + (idx + 1) * 2
            if not (idx == selected_rows):
                self._window.addstr(y, x_label, f"{row}:")
                self._window.addstr(y,
                                    x_values, f" {self.data[row]['default']}")

        y = screen_y_height - mid_count_m + (count_m + 1) * 2

        # Cancel and Submit button
        self.submit_button(x_label, y, values, selected_rows)

        # Form window with default values
        if selected_rows < count_m:
            y = (screen_y_height -
                 mid_count_m + (selected_rows + 1) * 2)

            self.on_attr(col_code_attr)
            self._window.addstr(y, x_label - 3, ">> ")
            self._window.addstr(y, x_label, f"{values[selected_rows]}:")

            # User want to edit some values from given form
            if edit:
                if ('validation' in self.data[values[selected_rows]]):
                    validate = self.data[values[selected_rows]]['validation']
                else:
                    validate = None
                user_content = TextBox(
                    self,
                    config.TBox.HEIGHT.value,
                    config.TBox.WIDTH.value,
                    y,
                    x_values + 1,
                    config.header_height
                ).create_textbox(
                    color_code,
                    self.data[values[selected_rows]]['default'],
                    validate
                )
                # Update user input in data
                self.data[values[selected_rows]]['default'] = user_content
            else:
                self._window.addstr(y, x_values,
                                    f" {self.data[values[selected_rows]]['default']}")  # noqa: E501
            self.off_attr(col_code_attr)

    def process_input(self, color_code):
        current_row = 0
        values = list(self.data.keys())

        while 1:
            key = self._window.getch()
            self._window.clear()
            # go up in list of input values
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1

            # go down in list of input values
            elif key == curses.KEY_DOWN and current_row < len(values):
                current_row += 1

            # from submit button, select cancel button from screen
            elif current_row == len(values) and key == curses.KEY_LEFT:
                current_row += 1

            # from cancel button, select submit button from  screen
            elif current_row == len(values) + 1 and key == curses.KEY_RIGHT:
                current_row -= 1

            # selected any input value to edit or selected buttons
            elif key == curses.KEY_ENTER or key in (config.Key.EXIT_1.value,
                                                    config.Key.EXIT_2.value):
                # if selected input values to edit
                if current_row < len(values) and current_row >= 0:
                    self._window.clear()
                    self.create_window(
                        color_code=color_code,
                        selected=current_row,
                        component=self._parent,
                        edit=True
                    )
                    self._window.refresh()
                # if selected submit button from screen
                elif current_row == len(values):
                    result, err = self.action()

                    if not result:
                        self._window.addstr(
                            4,
                            2,
                            f"Failed to set {self.component_type} Error: {err}"
                        )
                        self._window.refresh()
                        curses.napms(3000)
                    else:
                        formated_data = self.format_data()
                        win = SuccessWindow(self._window)
                        win.create_window(
                            color_code=2,
                            data=f"{self.component_type} : {formated_data}"
                        )
                        break
                # if selected cancel button from screen
                else:
                    break

            self._window.clear()
            self.create_window(color_code=color_code,
                               selected=current_row, component=self._parent)
            self._window.refresh()
