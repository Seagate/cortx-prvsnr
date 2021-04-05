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
from typing import Type

from . import Set
from ..errors import BadPillarDataError
from ..pillar import PillarKey, PillarResolver
from ..salt import local_minion_id, copy_to_file_roots, cmd_run as salt_cmd_run
from ..vendor import attr
from .. import inputs, values
from ..errors import (SaltCmdResultError, SWUpdateRepoSourceError)
from ..config import (PRVSNR_USER_FILES_SWUPDATE_REPOS_DIR, LOCAL_MINION,
                      REPO_CANDIDATE_NAME, RELEASE_INFO_FILE, ReleaseInfo)
from ..utils import load_yaml


logger = logging.getLogger(__name__)


# assumptions / limitations
#   - support only for ALL_MINIONS targetting TODO ??? why do you think so
#
#
# set/remove the repo:
#   - call repo reset logic for salt-minions:
#       - remove repo config for yum
#       - unmount repo if needed
#       - remove repo dir/iso file if needed TODO
#   - call repo reset logic for salt-master:
#       - remove local dir/file from salt user file root (if needed)
@attr.s(auto_attribs=True)
class SetSWUpdateRepo(Set):
    # TODO at least either pre or post should be defined
    input_type: Type[inputs.SWUpdateRepo] = inputs.SWUpdateRepo
    _REPO_DEST = PRVSNR_USER_FILES_SWUPDATE_REPOS_DIR
    _BASE_DIR_PILLAR = 'release/update/base_dir'

    def _prepare_repo_for_apply(self, repo: inputs.SWUpdateRepo,
                                enabled: bool = True):
        """Prepare repository for apply.

        Parameters
        ----------
        repo : inputs.SWUpdateRepo
            SW Update repository parameters
        enabled : bool
            Enable or not given repository

        Returns
        -------
        None

        """
        # if local - copy the repo to salt user file root
        # TODO consider to use symlink instead
        if repo.is_local():
            dest = self._REPO_DEST / repo.release

            if not repo.is_dir():  # iso file
                dest = dest.with_name(dest.name + '.iso')

            logger.debug(f"Copying {repo.source} to file roots")
            copy_to_file_roots(repo.source, dest)

            if not enabled:
                repo.repo_params = dict(enabled=False)

    def _get_mount_dir(self):
        """
        Return the base mount directory of ISO repo candidate based on pillars
        values configuration.

        Returns
        -------
        Path
            Path to repo candidate mount destination
        """
        update_dir = PillarKey(self._BASE_DIR_PILLAR)

        pillar = PillarResolver(LOCAL_MINION).get((update_dir,))

        pillar = pillar.get(local_minion_id())  # type: dict

        if (not pillar[update_dir] or
                pillar[update_dir] is values.MISSED):
            raise BadPillarDataError('value for '
                                     f'{update_dir.keypath} '
                                     'is not specified')

        return Path(pillar[update_dir])

    @staticmethod
    def _does_repo_exist(release: str) -> bool:
        """
        Check if passed `release` repo is listed among yum repositories
        (enabled or disabled)

        Parameters
        ----------
        release : str
            Release to check existence

        Returns
        -------
        bool
            True if `release` listed in yum repositories
        """
        # From yum manpage:
        # You  can  pass repo id or name arguments, or wildcards which to match
        # against both of those. However if the id or name matches exactly
        # then the repo will be listed even if you are listing enabled repos
        # and it is disabled.
        cmd = (f"yum repoinfo {release} 2>/dev/null | grep '^Repo\\-id' | "
               "awk -F ':' '{ print $NF }'")

        res = salt_cmd_run(cmd, targets=local_minion_id(),
                           fun_kwargs=dict(python_shell=True))

        find_repo = res[local_minion_id()].strip().split("/")[0]

        if find_repo:
            logger.debug(f"Found '{release}' repository in repolist")
        else:
            logger.debug(f"Didn't find '{release}' repository in repolist")

        return bool(find_repo)

    @staticmethod
    def _is_repo_enabled(release) -> bool:
        """
        Verifies if `release` repo listed in enabled yum repo list

        Parameters
        ----------
        release
            repo release for check

        Returns
        -------
        bool
            True if `release` listed in enabled yum repo list and False
            otherwise
        """
        cmd = (
            "yum repoinfo enabled -q 2>/dev/null | grep '^Repo\\-id' "
            "| awk  -F ':' '{print $NF}'"
        )
        res = salt_cmd_run(
            cmd, targets=local_minion_id(), fun_kwargs=dict(python_shell=True)
        )
        repos = [
            repo.strip().split('/')[0]
            for repo in res[local_minion_id()].split()
        ]
        logger.debug(f"Found enabled repositories: {repos}")
        return release in repos

    @staticmethod
    def _check_repo_is_valid(release, repo_name="sw_update"):
        """
        Validate if provided `release` repo is well-formed yum repository

        Parameters
        ----------
        release
            repo release for check
        repo_name: str
            repository name. Default: "sw_update"

        Returns
        -------
        None
            None if the repo is correct

        Raises
        ------
        SaltCmdResultError
            If `release` repo malformed.

        """
        cmd = (f"yum --disablerepo='*' --enablerepo='{repo_name}_{release}' "
               "list available")

        salt_cmd_run(cmd, targets=LOCAL_MINION)

    def dynamic_validation(self, params: inputs.SWUpdateRepo, targets: str):  # noqa: C901, E501
        repo = params

        if repo.is_special():
            logger.info(
                "Skipping update repo validation for special value: "
                f"{repo.source}"
            )
            return

        logger.info(
            f"Validating update repo: release {repo.release}, "
            f"source {repo.source}"
        )

        candidate_repo = inputs.SWUpdateRepo(REPO_CANDIDATE_NAME, repo.source)

        # TODO IMPROVE VALIDATION EOS-14350
        #   - there is no other candidate that is being verified:
        #     if found makes sense to raise an error in case the other
        #     logic is still running, if not - forcibly remove the previous
        #     candidate
        #   - after first mount 'sw_update_candidate' listed in disabled repos
        if self._does_repo_exist(f'sw_update_{candidate_repo.release}'):
            logger.warning(
                'other repo candidate was found, proceeding with force removal'
            )
            # TODO IMPROVE: it is not enough it may lead to locks when
            #  provisioner doesn't unmount `sw_update_candidate` repo
            # raise SWUpdateError(reason="Other repo candidate was found")

        # TODO IMPROVE
        #   - makes sense to try that only on local minion,
        #     currently it's not convenient since may lead to
        #     mess in release.sls pillar between all and specific
        #     minions
        try:
            logger.debug("Configuring update candidate repo for validation")
            self._prepare_repo_for_apply(candidate_repo, enabled=False)

            self._apply(candidate_repo, targets=targets)

            # general check from pkg manager point of view
            try:
                self._check_repo_is_valid(candidate_repo.release)
            except SaltCmdResultError as exc:
                raise SWUpdateRepoSourceError(
                    str(repo.source), f"malformed repo: '{exc}'"
                )

            # TODO: take it from pillar
            # the repo includes metadata file
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

            # TODO IMPROVE
            #   - new version is higher then currently installed

            # Optional: try to get current version of the repository
            # TODO: use digit-character regex to retrieve repository release
            # cmd = ('yum repoinfo enabled | '
            #        'sed -rn "s/Repo-id\\s+:.*sw_update_(.*)$/\\1/p"')

            repo.release = release

        finally:
            # remove the repo
            candidate_repo.source = values.UNDEFINED
            logger.info("Post-validation cleanup")
            self._apply(candidate_repo, targets=targets)

        return repo.metadata

    # TODO rollback
    def _run(self, params: inputs.SWUpdateRepo, targets: str):
        repo = params

        # TODO remove that block once that check fails the dynamic validation
        if self._is_repo_enabled(f'sw_update_{repo.release}'):
            logger.warning(
                "removing already enabled repository "
                f"for the '{repo.release}' release"
            )
            _repo = inputs.SWUpdateRepo(
                repo.release, values.UNDEFINED
            )
            self._apply(_repo, targets=targets)

        logger.info(f"Configuring update repo: release {repo.release}")
        self._prepare_repo_for_apply(repo, enabled=True)

        # call default set logic (set pillar, call related states)
        self._apply(repo, targets=targets)
        return repo.metadata
