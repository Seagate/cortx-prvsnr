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


logger = logging.getLogger(__name__)
_mod = sys.modules[__name__]


@attr.s(auto_attribs=True)
class ProvisionerAPI(Resource):
    name = 'provisioner'


class ProvisionerAPISLS(ResourceSLS):
    resource = ProvisionerAPI


@attr.s(auto_attribs=True)
class Install(ProvisionerAPISLS):
    name = 'install'
    state_name = 'provisioner.api.install'

    local: bool = False

    def setup_roots(self, targets):
        self.pillar_inline = {
            'api_distr': (
                'pip' if self.local == 'local' else 'pkg'
            )
        }
