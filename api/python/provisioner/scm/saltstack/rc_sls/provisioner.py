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

from provisioner.vendor import attr
from provisioner import config, utils

from provisioner.values import UNCHANGED, MISSED
from provisioner.resources import provisioner

from .base import ResourceCortxSLS


logger = logging.getLogger(__name__)


@attr.s
class ProvisionerSLS(ResourceCortxSLS):
    _base_sls = 'provisioner/core'

    def __attrs_post_init__(self):
        """No Ops."""


@attr.s
class ProvisionerInstallSLS(ProvisionerSLS):
    sls = 'install.package'
    state_t = provisioner.ProvisionerInstall


@attr.s
class ProvisionerInstallLocalSLS(ProvisionerSLS):
    sls = 'install.local'
    state_t = provisioner.ProvisionerInstallLocal

    def __attrs_post_init__(self):
        if (
            not (self.state.repo_tgz or self.state.repo_path)
            and not self.state.repo_tgz_root_path.exists()
        ):
            raise ValueError(
                "Either 'repo_tgz' or 'repo_path' should be specified"
            )

    @property
    def repo_tgz_root_path(self):
        return self.fileroot_path('repo.tgz')

    def _prepare_repo(self):
        if self.state.repo_tgz:
            logger.info(
                f"Using '{self.state.repo_tgz}' as a repo source archive"
            )
            self.fileroot_copy(self.state.repo_tgz, 'repo.tgz')
        elif self.state.repo_path:
            logger.info(
                f"Preparing local repo '{self.state.repo_path}'"
                f" of version '{self.state.repo_version}' for a setup"
            )

            # ensure parent dirs exists in profile file root
            self.repo_tgz_root_path.parent.mkdir(parents=True, exist_ok=True)

            utils.repo_tgz(
                self.repo_tgz_root_path,
                project_path=self.state.repo_path,
                version=self.state.repo_version,
                # TODO FIXME hard-coded
                include_dirs=['pillar', 'srv', 'files', 'api', 'cli']
            )

    @property
    def install_dir(self):
        res = next(iter(self.pillar.values())).get('install_dir')
        return (None if (not res or res is MISSED) else res)

    def setup_roots(self):
        super().setup_roots()

        self._prepare_repo()

        logger.info("Preparing pillars")
        if self.state.install_dir is UNCHANGED:
            if not self.install_dir:
                self.state.install_dir = config.PRVSNR_ROOT_DIR

        md5_hash = utils.calc_hash(
            self.repo_tgz_root_path, hash_type=config.HashType.MD5
        ).hexdigest()

        pillar = {
            'install_dir': self.state.install_dir,
            'repo': dict(tgz=dict(hash=f"md5={md5_hash}"))
        }
        self.pillar_set(pillar, expand=True)


# PROVISIONER API #

@attr.s
class ProvisionerAPISLS(ResourceCortxSLS):
    _base_sls = 'provisioner/api'

    def __attrs_post_init__(self):
        """No Ops."""


@attr.s
class ProvisionerAPIInstallSLS(ProvisionerAPISLS):
    sls = 'install'
    state_t = provisioner.ProvisionerAPIInstall

    @property
    def install_dir(self):
        res = next(iter(self.pillar.values())).get('install_dir')
        return (None if (not res or res is MISSED) else res)

    def setup_roots(self):
        super().setup_roots()

        self.pillar_inline['inline']['provisioner'] = dict(
            api=dict(distr=self.state.api_distr)
        )
