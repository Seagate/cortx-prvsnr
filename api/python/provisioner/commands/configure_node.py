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

import logging
from typing import Type
from pathlib import Path
from .. import inputs
from . import CommandParserFillerMixin
from ..config import CONFIG_MODULE_DIR
from ..vendor import attr
from ..utils import run_subprocess_cmd
from ..errors import ProvisionerError


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ConfigureNode(CommandParserFillerMixin):

    """API to trigger TUI for node configuration"""

    input_type: Type[inputs.NoParams] = inputs.NoParams

    def run(self, **kwargs):
        ui_script_path = str(CONFIG_MODULE_DIR / 'ui/main.py')

        if not Path(ui_script_path).is_file():
            raise ProvisionerError(f'{ui_script_path} file is missing')

        run_subprocess_cmd([f"python3 {ui_script_path}"],
                           shell=True, stdout=None, stderr=None)
        return
