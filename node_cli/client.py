# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

from importlib import import_module


class Client:
    """ Base class for invoking business logic functionality """

    def __init__(self, url):
        self._url = url

    def call(self, command):
        pass


class CliClient(Client):
    """Class Handles Direct Calls for CLI"""
    def __init__(self):
        super(CliClient, self).__init__(None)

    def call(self, command):
        module_obj = import_module(command.comm.get("target"))
        command_args = list(command.options.keys())
        exclude_args = ['format', 'comm', 'output',
                        'need_confirmation', 'sub_command_name']
        command_args = {arg: command.options.get(arg)
                        for arg in command.options.keys()
                        if arg not in exclude_args}

        if command.comm.get("class", None):
            if command.comm.get("is_static", False):
                target = getattr(module_obj, command.comm.get("class"))
            else:
                target = getattr(module_obj, command.comm.get("class"))()
        else:
            target = module_obj
        return getattr(target, command.comm.get("method"))(**command_args)
