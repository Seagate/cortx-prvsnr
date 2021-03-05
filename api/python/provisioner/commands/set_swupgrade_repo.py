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

from provisioner.pillar import PillarKey, PillarResolver

from ..salt import copy_to_file_roots, local_minion_id
from .set_swupdate_repo import SetSWUpdateRepo
from .. import inputs, values
from ..config import (REPO_CANDIDATE_NAME, IS_REPO_KEY, RELEASE_INFO_FILE,
                      ReleaseInfo, PRVSNR_USER_FILEROOT_DIR, InstallType)
from ..errors import SaltCmdResultError, SWUpdateRepoSourceError
from ..utils import load_yaml

logger = logging.getLogger(__name__)


class SetSWUpgradeRepo(SetSWUpdateRepo):

    _BASE_DIR_PILLAR = "release/upgrade/base_dir"
    _INSTALL_TYPE_PILLAR_KEY = "release/install_type"

    def _configure_install_type(self, install_type: str) -> PillarKey:
        """
        Configure the installation type for SW upgrade

        Parameters
        ----------
        install_type: str
            value for `install_type` pillar key

        Returns
        -------
        PillarKey
            PillarKey for the further `install_type` pillar update

        """
        install_type_path = PillarKey(self._INSTALL_TYPE_PILLAR_KEY)
        return inputs.PillarInputBase.from_args(
                                        keypath=install_type_path,
                                        value=install_type)

    def _get_current_install_type(self) -> str:
        """
        Get current install type for the local minion

        Returns
        -------
        str
            return `release/install_type` value for backup

        """
        pillar_path = PillarKey(self._INSTALL_TYPE_PILLAR_KEY)
        pillar = PillarResolver(local_minion_id()).get([pillar_path])

        for target, _pillar in pillar.items():
            if (not _pillar[pillar_path]
                    or _pillar[pillar_path] is values.MISSED):
                raise ValueError("value is not specified for "
                                 f"'{pillar_path}' and target '{target}'")
            else:
                return _pillar[pillar_path]

    @staticmethod
    def _prepare_single_iso_for_apply(repo: inputs.SWUpgradeRepo):
        """Prepare repository for apply.

        Parameters
        ----------
        repo : inputs.SWUpgrade
            SW Update repository parameters

        Returns
        -------
        None

        """
        logger.debug(f"Copy single ISO for SW upgrade to salt "
                     f"roots for release='{repo.release}'")
        # if local - copy the repo to salt user file root
        # TODO consider to use symlink instead
        if repo.is_local():
            dest = PRVSNR_USER_FILEROOT_DIR / repo.release

            if not repo.is_dir():  # iso file
                dest = dest.with_name(dest.name + '.iso')

            logger.debug(f"Copying {repo.source} to file roots")
            copy_to_file_roots(repo.source, dest)

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
            self._check_repo_is_valid(release, f"{repo_name}")
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

        install_type_backup = self._get_current_install_type()
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

            self._prepare_single_iso_for_apply(candidate_repo)

            install_type = self._configure_install_type(
                                                    InstallType.UPGRADE.name)
            base_dir = self._get_mount_dir()
            candidate_repo.target_build = base_dir

            logger.debug("Configure pillars and apply states for "
                         "candidate SW upgrade ISO")
            self._apply(candidate_repo, install_type, targets=targets)

            iso_mount_dir = base_dir / REPO_CANDIDATE_NAME

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

            repo_map = candidate_repo.pillar_value
            for dir_entry in (entry for entry in Path(iso_mount_dir).iterdir()
                              if entry.is_dir()):
                repo_name = f"{dir_entry.name}_{candidate_repo.release}"
                repo_info = repo_map.get(repo_name, None)

                if repo_info is None:
                    raise SWUpdateRepoSourceError(
                                    str(repo.source),
                                    "Unexpected repository in single ISO: "
                                    f"{dir_entry.name}")
                if repo_info[IS_REPO_KEY]:
                    self._single_repo_validation(candidate_repo.release,
                                                 dir_entry.name)

            repo.release = release

        finally:
            # remove the repo
            candidate_repo.source = values.UNDEFINED

            install_type = self._configure_install_type(install_type_backup)
            logger.info("Post-validation cleanup")
            self._apply(candidate_repo, install_type, targets=targets)

        return repo.metadata

    def _run(self, params: inputs.SWUpgradeRepo, targets: str):
        repo = params

        base_dir = self._get_mount_dir()
        repo.target_build = base_dir

        install_type = self._configure_install_type(InstallType.UPGRADE.name)

        # TODO remove that block once that check fails the dynamic validation
        if self._is_repo_enabled(f'sw_update_{repo.release}'):
            logger.warning(
                "removing already enabled repository "
                f"for the '{repo.release}' release"
            )
            _repo = inputs.SWUpgradeRepo(repo.release, values.UNDEFINED)
            self._apply(_repo, targets=targets)

        logger.info(f"Configuring update repo: release {repo.release}")
        self._prepare_single_iso_for_apply(repo)

        # call default set logic (set pillar, call related states)
        self._apply(repo, install_type, targets=targets)
        return repo.metadata
