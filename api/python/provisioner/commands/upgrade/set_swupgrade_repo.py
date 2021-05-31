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
import tempfile
from pathlib import Path
from typing import Type, Union
import requests
from configparser import ConfigParser

from provisioner.commands.upgrade import CheckISOAuthenticity
from provisioner.salt import copy_to_file_roots, cmd_run, local_minion_id
from ..set_swupdate_repo import SetSWUpdateRepo
from .. import inputs, values
from provisioner.config import (REPO_CANDIDATE_NAME,
                                IS_REPO_KEY,
                                RELEASE_INFO_FILE,
                                THIRD_PARTY_RELEASE_INFO_FILE,
                                ReleaseInfo,
                                PRVSNR_USER_FILES_SWUPGRADE_REPOS_DIR,
                                CORTX_ISO_DIR,
                                CORTX_3RD_PARTY_ISO_DIR,
                                CORTX_PYTHON_ISO_DIR,
                                OS_ISO_DIR, HashType,
                                PIP_CONFIG_FILE,
                                SWUpgradeInfoFields,
                                ISOValidationFields,
                                CheckVerdict
                                )
from provisioner.errors import (SaltCmdResultError, SWUpdateRepoSourceError,
                                ValidationError
                                )
from provisioner.utils import (load_yaml,
                               load_checksum_from_file,
                               load_checksum_from_str,
                               HashInfo, load_yaml_str
                               )
from ..validator import (DirValidator,
                         FileValidator,
                         FileSchemeValidator,
                         ReleaseInfoValidator,
                         YumRepoDataValidator,
                         HashSumValidator)
from provisioner.vendor import attr


logger = logging.getLogger(__name__)


# NOTE: keys can be either Path object or strings
SW_UPGRADE_BUNDLE_SCHEME = {
    CORTX_3RD_PARTY_ISO_DIR: DirValidator(
        {
            THIRD_PARTY_RELEASE_INFO_FILE: ReleaseInfoValidator(),
            "repodata": YumRepoDataValidator(),
        },
        required=False),
    CORTX_ISO_DIR: DirValidator(
        {
            RELEASE_INFO_FILE: ReleaseInfoValidator(),
            "repodata": YumRepoDataValidator(),
        },
        required=True),
    CORTX_PYTHON_ISO_DIR: DirValidator(
        {
            "index.html": FileValidator(required=True)
        },
        required=False),
    OS_ISO_DIR: DirValidator(
        {
            RELEASE_INFO_FILE: ReleaseInfoValidator(required=False),
            "repodata": YumRepoDataValidator(),
        },
        required=False)
}


@attr.s(auto_attribs=True)
class CortxISOInfo:
    """
    Result class that aggregates information about Cortx repository and its
    packages.
    """
    _prvsnr_type_ = True

    packages: dict = attr.ib(validator=attr.validators.instance_of(dict))
    metadata: dict = attr.ib(validator=attr.validators.instance_of(dict))

    def __str__(self):
        return f"{{'packages': {self.packages}, 'metadata': {self.metadata}}}"


@attr.s(auto_attribs=True)
class SetSWUpgradeRepo(SetSWUpdateRepo):

    input_type: Type[inputs.SWUpgradeRepo] = inputs.SWUpgradeRepo
    _BASE_DIR_PILLAR = "release/upgrade/base_dir"

    @staticmethod
    def _prepare_single_iso_for_apply(repo: inputs.SWUpgradeRepo):
        """Prepare repository for apply.

        Parameters
        ----------
        repo : inputs.SWUpgradeRepo
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
            dest = PRVSNR_USER_FILES_SWUPGRADE_REPOS_DIR / repo.release

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
            self._check_repo_is_valid(REPO_CANDIDATE_NAME,
                                      f"sw_upgrade_{repo_name}")
        except SaltCmdResultError as exc:
            raise SWUpdateRepoSourceError(repo_name,
                                          f"malformed repo: '{exc}'")

        # there is no the same release repo is already active
        if self._is_repo_enabled(f'sw_upgrade_{repo_name}_{release}'):
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
                        "SW upgrade repository for the release "
                        f"'{release}' has been already enabled"
                    )
                )

    @staticmethod
    def _validate_python_index(index_path: Path):
        """
        Perform the dynamic validation for SW upgrade Python index by
        the given index path `index_path`

        Parameters
        ----------
        index_path: Path
            Path to the SW upgrade Python index

        Returns
        -------
        None

        Raises
        ------
        SWUpdateRepoSourceError
            If Python index validation fails

        """
        logger.debug("Start Python index validation")
        test_package_name = next(index_path.iterdir()).name
        with tempfile.TemporaryDirectory() as tmp_dir:
            cmd = (f"pip3 download {test_package_name} --dest={tmp_dir}/ "
                   f"--index-url file://{index_path.resolve()}")
            try:
                cmd_run(cmd, targets=local_minion_id(),
                        fun_kwargs=dict(python_shell=True))
            except Exception as e:
                raise SWUpdateRepoSourceError(
                    index_path, "Python index validation failed: "f"{e}")

        logger.debug("Python index validation succeeded")

    @staticmethod
    def _get_hash_params(
            params: inputs.SWUpgradeRepo) -> HashInfo:
        """
        Parse and validate the provided hash parameters

        Parameters
        ----------
        params: Type[inputs.SWUpgradeRepo]
            input parameters which contain the hash parameters

        Returns
        -------
        HashInfo
            Returns `HashInfo` object with hash_sum, hash_type and filename
            data about checksum

        """
        hash_info = None

        if Path(params.hash).exists():
            _data = load_checksum_from_file(Path(params.hash))
            hash_info = _data

        if hash_info is not None:
            return hash_info

        hash_info = load_checksum_from_str(params.hash)

        if hash_info.hash_type is None and params.hash_type is not None:
            try:
                hash_info.hash_type = HashType(params.hash_type)
            except ValueError:
                logger.warning("Unexpected `hash-type` parameter value: "
                               f"{params.hash_type}")

        return hash_info

    def _pre_repo_validation(self, params: inputs.SWUpgradeRepo,
                             dry_run: bool = False):
        """
        SW upgrade repository pre-validation.

        Parameters
        ----------
        params: inputs.SWUpgradeRepo
            Input repository parameters
        dry_run: bool
            If this parameter is set to `True` this method skips some
            validations and returns only SW upgrade ISO bundle metadata
            (content of RELEASE.INFO).

        Raises
        ------
        SWUpdateRepoSourceError:
            Raise this exception if candidate repository validation fails

        """
        if not params.is_remote():
            if params.sig_file:
                logger.info("File with ISO signature is specified. Start GPG "
                            "signature validation for the ISO")

                # NOTE: We use CheckISOAuthenticity class instead of
                #  AuthenticityValidator to import GPG public key if
                #  `import_pub_key` is specified
                auth_validator = CheckISOAuthenticity()
                res = auth_validator.run(iso_path=params.source,
                                         sig_file=params.sig_file,
                                         gpg_pub_key=params.gpg_pub_key,
                                         import_pub_key=params.import_pub_key)

                if (res[ISOValidationFields.STATUS.value] ==
                        CheckVerdict.FAIL.value):
                    logger.warning(f"ISO signature validation is failed: "
                                   f"'{res[ISOValidationFields.MSG.value]}'")
                    raise SWUpdateRepoSourceError(
                        str(params.source),
                        "ISO signature validation error occurred: "
                        f"'{res[ISOValidationFields.MSG.value]}'"
                    )
                else:
                    logger.info('ISO signature validation succeeded')
            elif params.hash:
                logger.warning('Only integrity check is available.')
                logger.info("`hash` parameter is setup. Start checksum "
                            "validation for the whole ISO file")
                hash_info = self._get_hash_params(params)
                upgrade_bundle_hash_validator = HashSumValidator(
                    hash_sum=hash_info.hash_sum,
                    hash_type=hash_info.hash_type)

                try:
                    upgrade_bundle_hash_validator.validate(params.source)
                except ValidationError as e:
                    logger.warning(f"Check sum validation error occurred: {e}")
                    raise SWUpdateRepoSourceError(
                        str(params.source),
                        f"Check sum validation error occurred: '{e}'"
                    ) from e
                else:
                    logger.info('Check sum validation succeeded')
            else:
                logger.warning('Neither authenticity nor integrity validation'
                               'is available')
        # TODO IMPROVE VALIDATION EOS-14350
        #   - there is no other candidate that is being verified:
        #     if found makes sense to raise an error in case the other
        #     logic is still running, if not - forcibly remove the previous
        #     candidate
        #   - after first mount 'sw_update_candidate' listed in disabled repos
        # NOTE: yum repoinfo supports the wildcards in the name of a searching
        #  repository
        if not dry_run and self._does_repo_exist(
                    f'sw_upgrade_*_{params.release}'):
            logger.warning(
              'other repo candidate was found, proceeding with force removal'
            )
        # TODO IMPROVE: it is not enough it may lead to locks when
        #  provisioner doesn't unmount `sw_update_candidate` repo
        # raise SWUpdateError(reason="Other repo candidate was found")

    @staticmethod
    def _base_repo_validation(candidate_repo: inputs.SWUpgradeRepo,
                              base_dir: Path, dry_run: bool = False):
        """
        Base SW upgrade repository validation.

        Parameters
        ----------
        candidate_repo: inputs.SWUpgradeRepo
            Candidate SW upgrade repository parameters
        base_dir: Path
            Path to base SW upgrade directory
        dry_run: bool
            If this parameter is set to `True` this method skips some
            validations and returns only SW upgrade ISO bundle metadata
            (content of RELEASE.INFO).

        Returns
        -------
        dict:
            return SW upgrade candidate metadata

        Raises
        -------
        SWUpdateRepoSourceError:
            Raise this exception if candidate repository validation fails

        """
        if not candidate_repo.is_remote():
            iso_mount_dir = base_dir / REPO_CANDIDATE_NAME

            if not dry_run:
                sw_upgrade_bundle_validator = FileSchemeValidator(
                    SW_UPGRADE_BUNDLE_SCHEME
                )

                try:
                    sw_upgrade_bundle_validator.validate(iso_mount_dir)
                except ValidationError as e:
                    logger.debug(
                        f"Catalog structure validation error occurred: {e}"
                    )
                    raise SWUpdateRepoSourceError(
                        str(candidate_repo.source),
                        f"Catalog structure validation error occurred:{e}"
                    ) from e
                else:
                    logger.info("Catalog structure validation succeeded")

    def _post_repo_validation(self, candidate_repo: inputs.SWUpgradeRepo,
                              base_dir: Path, dry_run: bool = False):
        """
        Post validation of SW upgrade repository.

        Parameters
        ----------
        candidate_repo: inputs.SWUpgradeRepo
            Candidate SW upgrade repository parameters
        base_dir: Path
            Path to base SW upgrade directory
        dry_run: bool
            If this parameter is set to `True` this method skips some
            validations and returns only SW upgrade ISO bundle metadata
            (content of RELEASE.INFO).

        Raises
        ------
        SWUpdateRepoSourceError:
            Raise this exception if candidate repository validation fails

        """
        iso_mount_dir = base_dir / REPO_CANDIDATE_NAME
        if not dry_run and not candidate_repo.is_remote():
            # NOTE: this block only for local SW upgrade ISO bundles
            repo_map = candidate_repo.pillar_value
            for dir_entry in (entry for entry in
                              Path(iso_mount_dir).iterdir() if
                              entry.is_dir()):
                repo_info = repo_map.get(dir_entry.name, None)

                if repo_info is None:
                    raise SWUpdateRepoSourceError(
                        str(candidate_repo.source),
                        "Unexpected repository in single ISO: "
                        f"{dir_entry.name}")
                if repo_info[IS_REPO_KEY]:
                    self._single_repo_validation(candidate_repo.release,
                                                 dir_entry.name)
                elif dir_entry.name == CORTX_PYTHON_ISO_DIR:
                    self._validate_python_index(dir_entry)

    def dynamic_validation(self, params, targets: str,
                           dry_run: bool = False) -> Union[CortxISOInfo, None]:  # noqa: C901, E501
        """
        Validate single SW upgrade ISO structure.

        Parameters
        ----------
        params
            Input repository parameters
        targets: str
            Salt target to perform base mount and validation logic
        dry_run: bool
            If this parameter is set to `True` this method skips some
            validations and returns only SW upgrade ISO bundle metadata
            (content of RELEASE.INFO).

        Returns
        -------
        CortxISOInfo:
            return SW upgrade candidate metadata and version of packages or
            None repo source is special provisioner value

        Raises
        ------
        SWUpdateRepoSourceError:
            Raise this exception if candidate repository validation fails

        """
        repo = params
        base_dir = None

        if repo.is_special():
            logger.info("Skipping update repo validation for special value: "
                        f"{repo.source}")
            return

        logger.info(f"Validating upgrade repo: release '{REPO_CANDIDATE_NAME}'"
                    f", source {repo.source}")

        candidate_repo = inputs.SWUpgradeRepo(repo.source, REPO_CANDIDATE_NAME)

        self._pre_repo_validation(params, dry_run)

        try:
            logger.debug("Configuring upgrade candidate repo for validation")

            if not candidate_repo.is_remote():
                self._prepare_single_iso_for_apply(candidate_repo)

                base_dir = self._get_mount_dir()
                candidate_repo.target_build = base_dir

            candidate_repo.enabled = False

            logger.debug("Configure pillars and apply states for "
                         "candidate SW upgrade ISO")

            self._apply(candidate_repo, targets=targets, local=False)

            self._base_repo_validation(candidate_repo, base_dir, dry_run)

            if candidate_repo.is_remote():
                release_file = (f'{candidate_repo.source}/{CORTX_ISO_DIR}/'
                                f'{RELEASE_INFO_FILE}')
            else:
                iso_mount_dir = base_dir / REPO_CANDIDATE_NAME
                release_file = (f'{iso_mount_dir}/{CORTX_ISO_DIR}/'
                                f'{RELEASE_INFO_FILE}')

            metadata = self.load_metadata(release_file,
                                          candidate_repo.is_remote())

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

            candidate_repo.release = release

            self._post_repo_validation(candidate_repo, base_dir, dry_run)

            repo.release = release

            packages = self.get_packages_version(REPO_CANDIDATE_NAME)
        finally:
            # remove the repo
            candidate_repo.source = values.UNDEFINED

            logger.info("Post-validation cleanup")
            self._apply(candidate_repo, targets, local=False)

        return CortxISOInfo(packages=packages, metadata=repo.metadata)

    @staticmethod
    def _setup_python_index(repo: inputs.SWUpgradeRepo):
        """
        Setup Python index

        ----------
        Parameters
        repo: inputs.SWUpgradeRepo
            SW upgrade repository parameters

        """
        iso_mount_dir = repo.target_build / repo.release
        python_index_path = iso_mount_dir / CORTX_PYTHON_ISO_DIR
        if python_index_path in iso_mount_dir.iterdir():
            config = ConfigParser()
            config.read(PIP_CONFIG_FILE)
            extra_index_url = config['global'].get('extra-index-url', None)
            if extra_index_url:
                if str(python_index_path) not in extra_index_url:
                    # NOTE: if is needed to avoid index duplication
                    config['global']['extra-index-url'] = (
                        f"{extra_index_url}\n"
                        f"file://{python_index_path.resolve()}"
                    )
            else:
                config['global']['extra-index-url'] = (
                    f"file://{python_index_path.resolve()}"
                )

            with open(PIP_CONFIG_FILE, 'w') as conf_fh:
                config.write(conf_fh)

    def _run(self, params: inputs.SWUpgradeRepo, targets: str,
             local: bool = False):
        repo = params

        base_dir = self._get_mount_dir()
        repo.target_build = base_dir
        repo.enabled = True

        # TODO remove that block once that check fails the dynamic validation
        # FIXME: Currently we use 'os' repo is indicator
        if self._is_repo_enabled(f'sw_upgrade_os_{repo.release}'):
            logger.warning(
                "removing already enabled repository "
                f"for the '{repo.release}' release"
            )
            _repo = inputs.SWUpgradeRepo(values.UNDEFINED, repo.release)
            self._apply(_repo, targets=targets, local=local)

        logger.info(f"Configuring update repo: release {repo.release}")
        self._prepare_single_iso_for_apply(repo)

        # call default set logic (set pillar, call related states)
        self._apply(repo, targets, local=local)
        self._setup_python_index(repo)
        return repo.metadata

    @staticmethod
    def get_packages_version(release: str) -> dict:
        """
        Static method returns information about CORTX packages and
        their versions. Public method.

        Parameters
        ----------
        release : str
            SW upgrade repository version

        Returns
        -------
        dict
            return dictionary with CORTX packages and their versions

        """
        repo = f"sw_upgrade_{CORTX_ISO_DIR}_{release}"

        cmd = (f"yum repo-pkgs {repo} list 2>/dev/null | "
               f"grep '{repo}' | awk '{{print $1\" \"$2}}'")

        res = cmd_run(cmd, targets=local_minion_id(),
                      fun_kwargs=dict(python_shell=True))

        packages = res[local_minion_id()].strip()

        if packages:
            logger.debug(f"List of packages in repository '{repo}':"
                         f" {packages}")
        else:
            logger.debug(f"There are no packages in repository '{repo}'")

            return dict()

        packages = packages.split('\n')
        res = dict()
        # NOTE: Format is following
        # ```
        #  {
        #      'cortx-motr': {
        #             'version': '2.0.0-277',
        #          },
        #  }
        # ```
        #
        # TODO: EOS-20507: Along the with 'version', field we need to add
        #  'constraint version' field to provide necessary information about
        #  compatibility with old versions
        for entry in packages:
            pkg, ver = entry.split(" ")
            res[pkg] = {SWUpgradeInfoFields.VERSION.value: ver}

        return res

    @staticmethod
    def load_metadata(release_file_path: str, remote: bool = False):
        """

        Parameters
        ----------
        release_file_path
        remote

        Returns
        -------
        dict:
            dictionary with Cortx repository metadata (content of RELEASE.INFO
            file)

        """
        try:
            if remote:
                r = requests.get(release_file_path)
                metadata = load_yaml_str(r.content.decode("utf-8"))
            else:
                metadata = load_yaml(release_file_path)
        except Exception as exc:
            raise SWUpdateRepoSourceError(
                        str(release_file_path),
                        f"Failed to load '{release_file_path}' file: {exc}"
                    )

        return metadata
