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

from typing import Any, Union
import logging
from pathlib import Path

from .base import ResourceSLS

from provisioner.vendor import attr
from provisioner.resources import consul
from provisioner import config
from packaging.specifiers import SpecifierSet
from provisioner.attr_gen import attr_ib


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True, frozen=True)
class VersionRange:
    old_versions: Union[str, SpecifierSet] = attr_ib('version_specifier')
    new_version: Union[str, Path] = attr_ib('version')


migrations = {
    VersionRange('>=1.2.4,<1.4.0', '1.6.9'): {
        (1, config.ConfigLevelT.NODE): [
            'consul.upgrade.ACL_tokens',
            'consul.upgrade.1_6_9_config'
        ]
    },
    VersionRange('>=1.4.0,<1.4.0', '1.6.9'): {
        (1, config.ConfigLevelT.NODE): [
            'consul.upgrade.ACL_tokens'
        ]
    }
}


# XXX validation after setup
class ConsulUpgradeSLS(ResourceSLS):
    sls = None
    state_t = consul.ConsulUpgrade

    def setup_roots(self, targets):
        pass

    def run(self, targets: Any = config.ALL_TARGETS):
        for m_range, m_spec in migrations.items():
            if (
                self.state.new_version == m_range.new_version
                and m_range.old_versions.contains(self.state.old_version)
            ):
                break
        else:
            raise ValueError(
                f"Consul migration from '{self.state.old_version}'"
                f" to '{self.state.new_version}' is not supported"
            )

        self.sls = m_spec.get((self.state.iteration, self.state.level), None)
        super().run(targets)
