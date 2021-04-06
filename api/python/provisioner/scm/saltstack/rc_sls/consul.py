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

from typing import Union
import logging

from .base import ResourceSLS

from provisioner import config
from provisioner.vendor import attr
from provisioner.resources import consul
from packaging.specifiers import Version, SpecifierSet
from provisioner.attr_gen import attr_ib


logger = logging.getLogger(__name__)

VERSION_LATEST = 'latest'


@attr.s(auto_attribs=True, frozen=True)
class VersionRange:
    old_versions: Union[str, SpecifierSet] = attr_ib('version_specifier')
    new_version: Union[str, Version] = attr_ib('version')


@attr.s
class ConsulSLS(ResourceSLS):
    base_sls = 'resources.3rd_party.consul'

    def __attrs_post_init__(self):
        pass

    @property
    def version(self) -> str:
        return self.pillar.get('version', VERSION_LATEST)


@attr.s
class ConsulInstallSLS(ConsulSLS):
    sls = 'install'
    state_t = consul.ConsulInstall

    _version = str = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

        self._version = self.state.consul_version or VERSION_LATEST
        self.set_vendored(self.state.vendored)

    def setup_roots(self):
        super().setup_roots()
        self.pillar_set(dict(version=str(self._version)))


@attr.s
class ConsulConfigSLS(ConsulSLS):
    sls = 'config'
    state_t = consul.ConsulConfig

    def setup_roots(self):
        super().setup_roots()

        config = {}
        pillar = {'config': config, 'service': self.state.service}

        config['server'] = self.state.server
        config['bind_addr'] = str(self.state.bind_addr)
        config['bootstrap_expect'] = self.state.bootstrap_expect
        config['retry_join'] = self.state.retry_join

        self.pillar_set(pillar, expand=True)


@attr.s
class ConsulStartSLS(ConsulSLS):
    sls = 'start'
    state_t = consul.ConsulStart


@attr.s
class ConsulStopSLS(ConsulSLS):
    sls = 'stop'
    state_t = consul.ConsulStop


@attr.s
class ConsulTeardownSLS(ConsulSLS):
    sls = 'teardown'
    state_t = consul.ConsulTeardown

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

        if self.is_vendored:
            raise NotImplementedError(
                'teardown for Consul vendored setup is not supported yet'
            )


@attr.s
class ConsulSanityCheckSLS(ConsulSLS):
    sls = 'sanity_check'
    state_t = consul.ConsulSanityCheck

    @property
    def is_vendored(self) -> bool:
        return False


# XXX validation after setup
@attr.s
class ConsulUpgradeSLS(ConsulSLS):
    sls = None
    state_t = consul.ConsulUpgrade

    migrations = {
        VersionRange('<1.9.0', '1.9.1'): {
            (1, config.ConfigLevelT.NODE): [
                'migrations.1_9_0lt-1_9_0ge-1',
            ],
            (2, config.ConfigLevelT.NODE): [
                'migrations.1_9_0lt-1_9_0ge-2',
            ]
        }
    }

    @property
    def is_vendored(self) -> bool:
        return False

    def run(self):
        for m_range, m_spec in self.migrations.items():
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
        return super().run()
