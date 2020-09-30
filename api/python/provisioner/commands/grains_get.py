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

from . import CommandParserFillerMixin
from .. import inputs, ALL_MINIONS
from ..salt import function_run
from ..vendor import attr

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class GrainsGet(CommandParserFillerMixin):

    """Basic implementation for grains.item API for provisioner API."""

    input_type: Type[inputs.ParamsList] = inputs.ParamsList

    def run(self, *keys, targets=ALL_MINIONS) -> dict:
        """
        Base method to get grains data on nodes

        :param list keys: grains keys to fetch data from the nodes
        :param str targets: targets for grains fetching
        :return dict: dictionary with grains data
        """

        # TODO: grains_get improvements:
        #  - add grains param spec if necessary
        #  - create grains data classes as such as for pillars
        raw_res = function_run('grains.item', fun_args=keys, targets=targets)

        return raw_res
