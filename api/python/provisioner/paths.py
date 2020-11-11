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
class PillarPath:
    _base_dir: Path = attr.ib(
        converter=utils.converter_path,
        validator=utils.validator_path
    )
    _prefix: str = ''

    _host_dir_tmpl: str = attr.ib(init=False, default=None)
    _all_hosts_dir: Path = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        self._host_dir_tmpl = str(self.base_dir / 'minions/{minion_id}')
        self._all_hosts_dir = self.base_dir / 'groups/all'

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def prefix(self):
        return self._prefix

    @property
    def host_dir_tmpl(self):
        return self._host_dir_tmpl

    @property
    def all_hosts_dir(self):
        return self._all_hosts_dir


default_pillar = PillarPath(config.PRVSNR_PILLAR_DIR)

user_shared_pillar = PillarPath(
    config.PRVSNR_USER_PILLAR_DIR,
    config.PRVSNR_USER_PILLAR_PREFIX
)

user_local_pillar = PillarPath(
    config.PRVSNR_USER_LOCAL_PILLAR_DIR,
    config.PRVSNR_USER_LOCAL_PILLAR_PREFIX
)
