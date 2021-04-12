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
from pathlib import Path
import importlib
import logging


logger = logging.getLogger(__name__)

MODULE_PATH = Path(__file__)
MODULE_DIR = MODULE_PATH.resolve().parent


# def list_components():
#     from .base import ComponentBase
#
#     py_files = [
#         i for i in MODULE_DIR.glob('*.py')
#         if i.name != MODULE_PATH.name and i.name == 'test.py'
#     ]
#
#     modules = [
#         importlib.import_module(f'{__package__}.{f.stem}')
#         for f in py_files
#     ]
#
#     res = []
#
#     for mod in modules:
#         for _attr_name in dir(mod):
#             _attr = getattr(mod, _attr_name)
#             try:
#                 if not issubclass(_attr, ComponentBase):
#                     raise TypeError
#             except TypeError:
#                 pass  # not a class or not a subclass of ComponentBase
#             else:
#                 if _attr is not ComponentBase:
#                     if _attr.name:
#                         res.append(_attr)
#                     else:
#                         logger.debug(
#                             f"Ignoring component class {_attr}: "
#                             "undefined 'name'"
#                         )
