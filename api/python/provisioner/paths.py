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

from . import config, utils
from .vendor import attr


@attr.s(auto_attribs=True)
class RootPath:
    _root: Path = attr.ib(
        converter=utils.converter_path,
        validator=utils.validator_path
    )

    @property
    def root(self):
        return self._root


@attr.s(auto_attribs=True)
class FileRootPath(RootPath):

    def path(self, path):
        return self._root / path


@attr.s(auto_attribs=True)
class PillarPath(RootPath):
    _prefix: str = ''

    _host_dir_tmpl: str = attr.ib(init=False, default=None)
    _all_hosts_dir: Path = attr.ib(init=False, default=None)

    @staticmethod
    def add_merge_prefix(pillar_path: 'PillarPath', path: Path) -> Path:
        if path.name.startswith(pillar_path.prefix):
            return path
        else:
            return path.with_name(f"{pillar_path.prefix}{path.name}")

    def __attrs_post_init__(self):
        """Post init logic."""
        self._host_dir_tmpl = str(self.root / 'minions/{minion_id}')
        self._all_hosts_dir = self.root / 'groups/all'

    @property
    def prefix(self):
        return self._prefix

    @property
    def host_dir_tmpl(self):
        return self._host_dir_tmpl

    @property
    def all_hosts_dir(self):
        return self._all_hosts_dir

    def host_path(self, path, target: str):
        return self.add_merge_prefix(
            self, (
                Path(self.host_dir_tmpl.format(minion_id=target))
                / path
            )
        )

    def all_hosts_path(self, path):
        return self.add_merge_prefix(self, self.all_hosts_dir / path)


DEFAULT_FILEROOT = FileRootPath(config.PRVSNR_FILEROOT_DIR)
USER_SHARED_FILEROOT = FileRootPath(config.PRVSNR_USER_FILEROOT_DIR)
USER_LOCAL_FILEROOT = FileRootPath(config.PRVSNR_USER_LOCAL_FILEROOT_DIR)
GLUSTERFS_VOLUME_FILEROOT = FileRootPath(config.GLUSTERFS_VOLUME_FILEROOT_DIR)


DEFAULT_PILLAR = PillarPath(config.PRVSNR_PILLAR_DIR)

USER_SHARED_PILLAR = PillarPath(
    config.PRVSNR_USER_PILLAR_DIR,
    config.PRVSNR_USER_PILLAR_PREFIX
)

USER_LOCAL_PILLAR = PillarPath(
    config.PRVSNR_USER_LOCAL_PILLAR_DIR,
    config.PRVSNR_USER_LOCAL_PILLAR_PREFIX
)

GLUSTERFS_VOLUME_PILLAR = PillarPath(
    config.GLUSTERFS_VOLUME_PILLAR_DIR,
    config.PRVSNR_USER_PILLAR_PREFIX
)
