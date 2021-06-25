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
from typing import Type, Union, Optional
import json

from packaging import version

from provisioner import inputs, errors, utils
from provisioner.commands.upgrade.set_swupgrade_repo import (CortxISOInfo,
                                                             SetSWUpgradeRepo)
from provisioner.config import (
    REPO_CANDIDATE_NAME
)
from provisioner.pillar import PillarResolver, PillarKey

from provisioner.salt import local_minion_id
from provisioner.commands import CommandParserFillerMixin, commands
from provisioner.commands.release import CortxRelease
from provisioner.vendor import attr


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class GetSWUpgradeInfoArgs:
    iso_path: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "Path to SW upgrade single ISO bundle"
            }
        },
        validator=attr.validators.optional(utils.validator_path_exists),
        converter=utils.converter_path_resolved,
        default=None
    )
    release: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "SW upgrade repository release version"
            }
        },
        default=None
    )


@attr.s(auto_attribs=True)
class GetSWUpgradeInfo(CommandParserFillerMixin):
    """
    Base class that provides API for getting SW upgrade repository information.

    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = GetSWUpgradeInfoArgs

    @classmethod
    def cortx_version(
        cls,
        release_metadata: Optional[Union[str, dict]] = None,
        iso_path: str = None,
        release: str = None
    ):
        if release_metadata is None:
            try:
                release_metadata = cls().run(
                    iso_path=iso_path, release=release
                )
                if release_metadata is None:
                    return None
                release_metadata = release_metadata.metadata
            except errors.BadPillarDataError:
                return None  # NOTE: there are no configured SW upgrade repos

        if isinstance(release_metadata, str):
            release_metadata = json.loads(release_metadata)

        return CortxRelease(metadata=release_metadata).version

    @staticmethod
    def _get_set_swupgrade_repo_obj() -> SetSWUpgradeRepo:
        """
        Get SetSWUpgradeRepo instance

        Returns
        -------
        SetSWUpgradeRepo:
            return SetSWUpgradeRepo instance

        """
        # NOTE: get `SetSWUpgradeRepo` from list of commands since all
        #  objects are correctly defined (post- and pre- states)
        return commands['set_swupgrade_repo']

    def run(self, iso_path: str = None,
            release: str = None) -> Union[CortxISOInfo, None]:
        """
        Main function for Get SW Upgrade Repo command. Command returns
        information about CORTX packages and their versions.

        Parameters
        ----------
        iso_path: str
            Path to SW upgrade single ISO bundle
        release: str
            SW upgrade repository release version

        Returns
        -------
        CortxISOInfo:
            return instance of CortxISOInfo with CORTX packages versions and
            Cortx repo metadata

        """
        run_args = self._run_args_type(iso_path, release)

        local_minion = local_minion_id()
        set_swupgrade_repo = self._get_set_swupgrade_repo_obj()
        iso_version = None

        if run_args.iso_path is not None:
            # if the `iso_path` is set up, we ignore the `release` parameter
            return set_swupgrade_repo.run(run_args.iso_path, dry_run=True)

        if run_args.release is not None:
            cortx_release = CortxRelease(version=run_args.release)
        else:
            # NOTE: take the latest release from SW upgrade repositories

            # TODO: make get pillar API public and available for others to
            #  avoid code duplication
            pillar_path = 'release/upgrade/repos'
            pillars = PillarResolver(local_minion).get(
                [PillarKey(pillar_path)],
                fail_on_undefined=True
            )

            repos_info = pillars[local_minion][PillarKey(pillar_path)]
            upgrade_releases = list(repos_info.keys())

            upgrade_releases.remove(REPO_CANDIDATE_NAME)

            if not upgrade_releases:
                logger.warning("There are no set up SW upgrade repositories")
                return None

            # NOTE: Assumption: we expect that SW Upgrade release version
            # is formatted according to PEP-440
            run_args.release = max(upgrade_releases, key=version.parse)

            cortx_release = CortxRelease(version=run_args.release)

        iso_version = cortx_release.iso_version

        set_swupgrade_repo.set_source_version(iso_version)
        packages = set_swupgrade_repo.get_packages_version(run_args.release)

        return CortxISOInfo(
            packages=packages,
            metadata=cortx_release.metadata
        )
