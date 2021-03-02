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
from pathlib import Path

from .set_swupdate_repo import SetSWUpdateRepo
from .. import inputs, values
from ..config import (REPO_CANDIDATE_NAME, SW_UPGRADE_REPOS, YUM_REPO_TYPE,
                      PRVSNR_USER_FILES_SWUPGRADE_REPOS_DIR, RELEASE_INFO_FILE,
                      ReleaseInfo
                      )
from ..errors import SaltCmdResultError, SWUpdateRepoSourceError
from ..utils import load_yaml

logger = logging.getLogger(__name__)


class SetSWUpgradeRepo(SetSWUpdateRepo):

    _REPO_DEST = PRVSNR_USER_FILES_SWUPGRADE_REPOS_DIR
    _BASE_DIR_PILLAR = "release/upgrade/base_dir"

    def _single_repo_validation(self, release, repo_name):
        """
        Separate private method for basic single repo validations.

        Parameters
        ----------
        release:
            Single Upgrade ISO release version
        repo_name: str
            Repository name

        Returns
        -------

        """
        logger.info(f"Validate single SW upgrade repo '{repo_name}' "
                    f"of release {release}")

        # general check from pkg manager point of view
        try:
            self._check_repo_is_valid(release, f"sw_upgrade_{repo_name}")
        except SaltCmdResultError as exc:
            raise SWUpdateRepoSourceError(
                                        repo_name, f"malformed repo: '{exc}'")

        # there is no the same release repo is already active
        if self._is_repo_enabled(f'sw_update_{release}'):
            err_msg = (
                "SW update repository for the release "
                f"'{release}' has been already enabled"
            )
            logger.warning(err_msg)

            # TODO IMPROVE later raise and error
            if False:
                raise SWUpdateRepoSourceError(
                    # FIXME repo is undefined here
                    str(repo.source),
                    (
                        f"SW update repository for the release "
                        f"'{release}' has been already enabled"
                    )
                )

    def dynamic_validation(self, params: inputs.SWUpgradeRepo, targets: str):  # noqa: C901, E501
        """
        Validate single SW upgrade ISO structure.

        Parameters
        ----------
        params: inputs.SWUpgradeRepo
            Input repository parameters
        targets: str
            Salt target to perform base mount and validation logic

        Returns
        -------

        """
        repo = params

        if repo.is_special():
            logger.info("Skipping update repo validation for special value: "
                        f"{repo.source}")
            return

        logger.info(f"Validating upgrade repo: release {repo.release}, "
                    f"source {repo.source}")

        candidate_repo = inputs.SWUpgradeRepo(REPO_CANDIDATE_NAME, repo.source)
        # TODO IMPROVE VALIDATION EOS-14350
        #   - there is no other candidate that is being verified:
        #     if found makes sense to raise an error in case the other
        #     logic is still running, if not - forcibly remove the previous
        #     candidate
        #   - after first mount 'sw_update_candidate' listed in disabled repos
        # TODO: need to have logic for sw upgrade
        # if self._does_repo_exist(f'sw_update_{candidate_repo.release}'):
        #     logger.warning(
        #       'other repo candidate was found, proceeding with force removal'
        #     )
        # TODO IMPROVE: it is not enough it may lead to locks when
        #  provisioner doesn't unmount `sw_update_candidate` repo
        # raise SWUpdateError(reason="Other repo candidate was found")

        try:
            logger.debug("Configuring upgrade candidate repo for validation")
            self._prepare_repo_for_apply(candidate_repo, enabled=False)

            self._apply(candidate_repo, targets)

            iso_mount_dir = self._get_mount_dir() / REPO_CANDIDATE_NAME

            release_file = f'{iso_mount_dir}/{RELEASE_INFO_FILE}'
            try:
                metadata = load_yaml(release_file)
            except Exception as exc:
                raise SWUpdateRepoSourceError(
                    str(repo.source),
                    f"Failed to load '{RELEASE_INFO_FILE}' file: {exc}"
                )
            else:
                repo.metadata = metadata
                logger.debug(f"Resolved metadata {metadata}")

            # the metadata file includes release info
            # TODO IMPROVE: maybe it is good to verify that 'RELEASE'-field
            #  well formed
            release = metadata.get(ReleaseInfo.RELEASE.value, None)
            if release is None:
                try:
                    release = (
                        f'{metadata[ReleaseInfo.VERSION.value]}-'
                        f'{metadata[ReleaseInfo.BUILD.value]}'
                    )
                except KeyError:
                    raise SWUpdateRepoSourceError(
                        str(repo.source),
                        f"No release data found in '{RELEASE_INFO_FILE}'"
                    )

            for dir_entry in (entry for entry in Path(iso_mount_dir).iterdir()
                              if entry.is_dir()):
                repo_info = SW_UPGRADE_REPOS.get(dir_entry.name, None)
                if repo_info is None:
                    raise SWUpdateRepoSourceError(
                                    str(repo.source),
                                    "Unexpected repository in single ISO: "
                                    f"{dir_entry.name}")
                if repo_info[YUM_REPO_TYPE]:
                    self._single_repo_validation(candidate_repo.release,
                                                 dir_entry.name)

            repo.release = release

        finally:
            # remove the repo
            candidate_repo.source = values.UNDEFINED
            logger.info("Post-validation cleanup")
            self._apply(candidate_repo, targets)

        return repo.metadata
