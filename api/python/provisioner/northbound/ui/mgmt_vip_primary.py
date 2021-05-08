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
from . import config
from .mgmt_vip import MgmtVIPWindow
from .question_window import QuestionWindow


class IsPrimaryWindow(QuestionWindow):

    _question = "Is this the first node configured for this new cluster?"

    def yes_action(self):
        color_code = config.menu_color
        wd = MgmtVIPWindow(self._window)
        wd.create_window(
                            color_code=color_code,
                            component=self._parent
                        )

        if hasattr(wd, 'process_input'):
            wd.process_input(color_code=color_code)
