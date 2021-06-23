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

import json
import logging

from typing import Union, Optional, List, Type
from pathlib import Path

from provisioner.vendor import attr
from provisioner.attr_gen import attr_ib
from provisioner import config, inputs, utils, errors
from provisioner.salt import (
    local_minion_id,
    cmd_run
)
from provisioner.pillar import (
    PillarKey,
    PillarResolver
)
from provisioner.commands._basic import (
    CommandParserFillerMixin
)

from .release import CortxRelease

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class GetReleaseVersion(CommandParserFillerMixin):
    description = (
        "A command to get CORTX release."
    )

    factory: bool = attr_ib(cli_spec='release/factory', default=False)

    _installed_rpms: List = attr.ib(init=False, default=None)

    @classmethod
    def cortx_version(
        cls, release_metadata: Optional[Union[str, dict]] = None
    ):
        if release_metadata is None:
            release = cls().cortx_release()
        else:
            release = CortxRelease(metadata=release_metadata)

        return release.version

    @property
    def installed_rpms(self) -> List:
        if self._installed_rpms is None:
            exclude_rpms = 'cortx-py|prvsnr-cli|cortx-sspl-test'
            res = cmd_run(
                f"rpm -qa|grep '^cortx-'|grep -Ev '{exclude_rpms}'",
                targets=local_minion_id()
            )
            rpms = res[next(iter(res))].split("\n")
            self._installed_rpms = [f'{rpm}.rpm' for rpm in rpms if rpm]
        return self._installed_rpms

    def _get_rpms_from_release(self, source):
        return utils.load_yaml(source)['COMPONENTS']

    # TODO (deprecated) the following logic fails in many cases, e.g.:
    #       - installed pkg is not listed in upgrade bundle
    def _compare_rpms_info(self, release_rpms):
        return (release_rpms and
                set(self.installed_rpms).issubset(release_rpms))

    def _get_release_info_path(self):
        release_info = None
        update_repo = PillarKey('release/upgrade')
        pillar = PillarResolver(local_minion_id()).get([update_repo])
        pillar = next(iter(pillar.values()))
        upgrade_data = pillar[update_repo]
        base_dir = Path(upgrade_data['base_dir'])
        repos = upgrade_data['repos']
        for version in reversed(list(repos)):
            if version == config.REPO_CANDIDATE_NAME:
                continue
            release_info = base_dir / f'{version}/RELEASE.INFO'
            # Note. upgrade iso now may lack release file on top level
            if not release_info.exists():
                release_info = (
                    base_dir / f'{version}/{config.CORTX_ISO_DIR}/RELEASE.INFO'
                )
            if release_info.exists():
                release_rpms = self._get_rpms_from_release(release_info)
                if self._compare_rpms_info(release_rpms):
                    return release_info

    def cortx_release(self, factory=False):
        if factory:
            return CortxRelease.factory_release()

        if config.CORTX_RELEASE_INFO_PATH.exists():
            source = config.CORTX_RELEASE_INFO_PATH
        else:
            # fallback to legacy logic
            source = (
                self._get_release_info_path()
                or config.CORTX_RELEASE_FACTORY_INFO_PATH
            )

        if not source.exists():
            raise errors.ReleaseFileNotFoundError()

        return CortxRelease(metadata_url=source)

    def run(self, factory=False):
        return self.cortx_release(factory=factory).metadata


@attr.s(auto_attribs=True)
class GetReleaseVersionLegacy(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = None

    def run(self):
        return json.dumps(GetReleaseVersion().run(factory=False))


@attr.s(auto_attribs=True)
class GetFactoryVersionLegacy(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = None

    def run(self):
        return json.dumps(GetReleaseVersion().run(factory=True))
