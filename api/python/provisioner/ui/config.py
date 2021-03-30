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
from enum import Enum


class ColorCodes(Enum):
    BLACK_N_WHITE = 1
    GREEN_N_BLACK = 2
    RED_N_BLACK = 3
    GREEN_N_WHITE = 4


class Key(Enum):
    EXIT_1 = 10
    EXIT_2 = 13
    QUITE = 113


sub_menu_network = {"DHCP": 'hostname:HostnameWindow',
                    "Static": 'static_data:StaticNetworkWindow'}

sub_menu_mgmt_network = {"DHCP": 'hostname:HostnameWindow',
                         "Static": 'static_mgmt:StaticMGMTNetworkWindow'}

sub_menu_bmc_network = {"DHCP": 'hostname:HostnameWindow',
                        "Static": 'static_bmc:StaticBMCNetworkWindow'}

menu_network = {'Management Network': sub_menu_mgmt_network,
                'Data Network': sub_menu_network,
                'BMC Network IP': sub_menu_bmc_network,
                'Apply Network': 'hostname:HostnameWindow'}

menu = {
    'Set Hostname': 'hostname:HostnameWindow',
    'Setup Netowrk': menu_network,
    'Set Host Primary': 'is_primary:PrimaryWindow',
    'Setup storage': 'hostname:HostnameWindow',
    'Setup firewall': 'hostname:HostnameWindow',
    'Setup Time Server': 'hostname:HostnameWindow'
}


color_codes = {
    ColorCodes.BLACK_N_WHITE.value: [curses.COLOR_BLACK, curses.COLOR_WHITE],
    ColorCodes.GREEN_N_BLACK.value: [curses.COLOR_GREEN, curses.COLOR_BLACK],
    ColorCodes.RED_N_BLACK.value: [curses.COLOR_RED, curses.COLOR_BLACK],
    ColorCodes.GREEN_N_WHITE.value: [curses.COLOR_GREEN, curses.COLOR_WHITE]
}


error_color = ColorCodes.RED_N_BLACK.value
default_window_color = ColorCodes.GREEN_N_BLACK.value
menu_color = ColorCodes.GREEN_N_BLACK.value
default_menu_head = ColorCodes.BLACK_N_WHITE.value

tittle = "Lvye Rack II"
