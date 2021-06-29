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
from typing import Type, Union, Any
from urllib.parse import urlparse, unquote

from configparser import ConfigParser

from provisioner.vendor import attr
from provisioner.commands import Check
from provisioner.commands.upgrade import CheckISOAuthenticity
from provisioner.salt import copy_to_file_roots, cmd_run, local_minion_id
from provisioner.commands.set_swupdate_repo import SetSWUpdateRepo
from provisioner import inputs, values
from provisioner.config import (REPO_CANDIDATE_NAME,
                                IS_REPO_KEY,
                                RELEASE_INFO_FILE,
                                CORTX_RELEASE_INFO_FILE,
                                THIRD_PARTY_RELEASE_INFO_FILE,
                                PRVSNR_USER_FILES_SWUPGRADE_REPOS_DIR,
                                CORTX_ISO_DIR,
                                CORTX_3RD_PARTY_ISO_DIR,
                                CORTX_PYTHON_ISO_DIR,
                                OS_ISO_DIR, HashType,
                                PIP_CONFIG_FILE,
                                SWUpgradeInfoFields,
                                ISOValidationFields,
                                ISOVersion,
                                ISOKeywordsVer2 as ISOVer2,
                                UpgradeReposVer2,
                                CheckVerdict,
                                Checks
                                )
from provisioner.errors import (SaltCmdResultError, SWUpdateRepoSourceError,
                                ValidationError,
                                SWUpdateError
                                )
from provisioner.utils import (
    load_checksum_from_file,
    load_checksum_from_str,
    HashInfo
)
from provisioner.commands.validator import (
    DirValidator,
    FileValidator,
    FileSchemeValidator,
    ReleaseInfoValidator,
    ThirdPartyReleaseInfoValidator,
    YumRepoDataValidator,
    HashSumValidator
)
from provisioner.commands.release import CortxRelease


logger = logging.getLogger(__name__)


# NOTE: keys can be either Path object or strings
SW_UPGRADE_BUNDLE_SCHEME_VER1 = {
    CORTX_3RD_PARTY_ISO_DIR: DirValidator(
        {
            THIRD_PARTY_RELEASE_INFO_FILE: ThirdPartyReleaseInfoValidator(),
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


SW_UPGRADE_BUNDLE_SCHEME_VER2 = {
    RELEASE_INFO_FILE: ReleaseInfoValidator(),
    ISOVer2.FW: DirValidator(
        {
            ISOVer2.SERVER: DirValidator(
                required=False,
                empty=True
            ),
            ISOVer2.STORAGE: DirValidator(
                required=False,
                empty=True
            )
        },
        required=False,
        empty=True
    ),
    ISOVer2.OS: DirValidator(
        {
            ISOVer2.PATCHES: DirValidator(
                required=False,
                empty=True
            )
        },
        required=False,
        empty=True
    ),
    ISOVer2.SW: DirValidator(
        {
            ISOVer2.CORTX: DirValidator(
                {
                    CORTX_RELEASE_INFO_FILE: ReleaseInfoValidator(
                        required=True
                    ),
                    "repodata": YumRepoDataValidator()
                },
                required=True
            ),
            ISOVer2.EXTERNAL: DirValidator(
                {
                    THIRD_PARTY_RELEASE_INFO_FILE:
                        ThirdPartyReleaseInfoValidator(),
                    ISOVer2.PYTHON: DirValidator(
                        {
                            "index.html": FileValidator(required=True)
                        },
                        required=False,
                        empty=True),
                    ISOVer2.RPM: DirValidator(
                        {
                            ISOVer2.EPEL_7: DirValidator(
                                {
                                    "repodata": YumRepoDataValidator()
                                },
                                required=True
                            ),
                            ISOVer2.COMMONS: DirValidator(
                                {
                                    "repodata": YumRepoDataValidator()
                                },
                                required=False,
                                empty=True
                            ),
                            ISOVer2.PERFORMANCE: DirValidator(
                                {
                                    "repodata": YumRepoDataValidator()
                                },
                                required=False,
                                empty=True
                            )
                        },
                        required=True)
                },
                required=False,
                empty=True
            )
        },
        required=True
    )
}

SW_UPGRADE_BUNDLE_SCHEME = {
    ISOVersion.VERSION1: SW_UPGRADE_BUNDLE_SCHEME_VER1,
    ISOVersion.VERSION2: SW_UPGRADE_BUNDLE_SCHEME_VER2
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
class ProxyCommand:
    """Class implements the simple proxy pattern.

    Attributes
    ----------
    _proxy: Any
        Instance (class instance) that is responsible for proxy calls
        if base class doesn't implement the desired method.

    """

    _proxy: Any = attr.ib()

    def __getattr__(self, item):
        """
        Delegate method-call/attribute to the proxy object

        Parameters
        ----------
        item: str
            attribute name

        Returns
        -------
        Any:
           method or attribute of the proxy object

        """
        # NOTE: __getattr__ is called when item method is not defined in
        #  current class. Delegate call to proxy-object
        return self._proxy.__getattribute__(item)


class SetSWUpgradeRepoVer1(ProxyCommand):
    """This class implements specific methods for SW upgrade ISO of version 1.
    """

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
                    # FIXME upgrade iso may includes something strange for now
                    # raise SWUpdateRepoSourceError(
                    #     str(candidate_repo.source),
                    #     "Unexpected repository in single ISO: "
                    #     f"{dir_entry.name}")
                    logger.warning(
                        "Unexpected repository in single ISO: "
                        f"{dir_entry.name}"
                    )
                    continue
                if repo_info[IS_REPO_KEY]:
                    self._single_repo_validation(candidate_repo.release,
                                                 dir_entry.name)
                elif dir_entry.name == CORTX_PYTHON_ISO_DIR:
                    self._validate_python_index(dir_entry)

    @staticmethod
    def get_release_file_path(iso_root_dir: Path):
        """
        Compute the release file path

        Parameters
        ----------
        iso_root_dir: Path
            Root path for the SW upgrade ISO

        Returns
        -------
        str:
            Absolute path to the RELEASE.INFO file
        """
        return f'{iso_root_dir}/{CORTX_ISO_DIR}/{RELEASE_INFO_FILE}'


class SetSWUpgradeRepoVer2(ProxyCommand):
    """This class implements specific methods for SW upgrade ISO of version 2.
    """

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
        if not dry_run and not candidate_repo.is_remote():
            # NOTE: this block only for local SW upgrade ISO bundles
            for repo_name, repo_info in candidate_repo.pillar_value.items():
                res = urlparse(repo_info['source'])
                repo_path = Path(unquote(res.path))
                if repo_info[IS_REPO_KEY]:
                    if repo_path.exists() and any(repo_path.iterdir()):
                        # NOTE: start repo validation if path to the repo
                        #  exists and directory is not empty
                        self._single_repo_validation(candidate_repo.release,
                                                     repo_name)
                elif repo_name == ISOVer2.PYTHON:
                    self._validate_python_index(repo_path)

    @staticmethod
    def get_release_file_path(iso_root_dir: Path):
        """
        Compute the release file path

        Parameters
        ----------
        iso_root_dir: Path
            Root path for the SW upgrade ISO

        Returns
        -------
        str:
            Absolute path to the RELEASE.INFO file
        """
        return f'{iso_root_dir}/{RELEASE_INFO_FILE}'


@attr.s(auto_attribs=True)
class SetSWUpgradeRepo(SetSWUpdateRepo):

    input_type: Type[inputs.SWUpgradeRepo] = inputs.SWUpgradeRepo
    _BASE_DIR_PILLAR = "release/upgrade/base_dir"
    _version_proxy: dict = attr.ib(
        default=None
    )
    _source_version: ISOVersion = attr.ib(
        default=ISOVersion.VERSION1
    )

    def __attrs_post_init__(self):
        self._version_proxy = dict()
        self._version_proxy[ISOVersion.VERSION1] = SetSWUpgradeRepoVer1(self)
        self._version_proxy[ISOVersion.VERSION2] = SetSWUpgradeRepoVer2(self)

    def __getattr__(self, item):
        """
        This method defines behavior when item-method is not defined in scope
        of the current class

        Parameters
        ----------
        item: str
            attribute name

        Returns
        -------
        Any:
            attribute of proxy object

        """
        return self._version_proxy[self._source_version].__getattribute__(item)

    def set_source_version(self, version: Union[str, ISOVersion]):
        """
        Setup the SW upgrade ISO structure version

        Parameters
        ----------
        version: Union[str, ISOVersion]
            SW upgrade ISO structure version

        Returns
        -------
        None

        """
        self._source_version = ISOVersion(version)

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

            raise SWUpdateRepoSourceError(
                str(repo_name),
                (
                    f"SW upgrade repository '{repo_name}' for the release "
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
        if not index_path.exists() or not any(
                p for p in index_path.iterdir() if p.is_dir()):
            return

        pkgs = (p for p in index_path.iterdir() if p.is_dir())
        try:
            test_package_name = next(pkgs).name
        except StopIteration:
            logger.debug("Python index is empty, skip the validation")
            return

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

    @staticmethod
    def _check_iso_authenticity(params: inputs.SWUpgradeRepo):
        """
        SW upgrade repository pre-validation.

        Parameters
        ----------
        params

        Returns
        -------

        """
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

        if res[ISOValidationFields.STATUS.value] == CheckVerdict.FAIL.value:
            logger.warning(f"ISO signature validation is failed: "
                           f"'{res[ISOValidationFields.MSG.value]}'")
            raise SWUpdateRepoSourceError(
                str(params.source),
                "ISO signature validation error occurred: "
                f"'{res[ISOValidationFields.MSG.value]}'"
            )
        else:
            logger.info('ISO signature validation succeeded')

    @staticmethod
    def _check_iso_integrity(params: inputs.SWUpgradeRepo,
                             hash_info: HashInfo):
        """

        Parameters
        ----------
        params: inputs.SWUpgradeRepo

        hash_info: HashInfo

        Returns
        -------

        """
        upgrade_bundle_hash_validator = HashSumValidator(
            hash_sum=hash_info.hash_sum,
            hash_type=hash_info.hash_type
        )

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
            if params.sig_file is None:
                logger.info("Signature file is not specified")
                suffix = params.source.suffix + ".sig"
                params.sig_file = Path(str(params.source)).with_suffix(suffix)

                if not params.sig_file.exists():
                    raise SWUpdateRepoSourceError(
                        str(params.source),
                        f"Signature file '{params.sig_file}' is not found"
                    )

            self._check_iso_authenticity(params)

            if params.hash:
                logger.warning('Only integrity check is available.')
                logger.info("`hash` parameter is setup. Start checksum "
                            "validation for the whole ISO file")
                hash_info = self._get_hash_params(params)
                self._check_iso_integrity(params, hash_info)

        # TODO IMPROVE VALIDATION EOS-14350
        #   - there is no other candidate that is being verified:
        #     if found makes sense to raise an error in case the other
        #     logic is still running, if not - forcibly remove the previous
        #     candidate
        #   - after first mount 'sw_update_candidate' listed in disabled repos
        # NOTE: yum repoinfo supports the wildcards in the name of a searching
        #  repository
        if not dry_run and self._does_repo_exist(
            f'sw_upgrade_*_{params.release}'
        ):
            logger.warning(
              'other repo candidate was found, proceeding with force removal'
            )
        # TODO IMPROVE: it is not enough it may lead to locks when
        #  provisioner doesn't unmount `sw_update_candidate` repo
        # raise SWUpdateError(reason="Other repo candidate was found")

    def _base_repo_validation(self, candidate_repo: inputs.SWUpgradeRepo,
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
                    SW_UPGRADE_BUNDLE_SCHEME[self._source_version]
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

        checker = Check()
        try:
            check_res = checker.run(Checks.ACTIVE_UPGRADE_ISO.value)
        except Exception as e:
            logger.warning("During the detection of the active SW upgrade ISO "
                           f"error happened: {str(e)}")
        else:
            if check_res.is_failed:
                raise SWUpdateError("An active SW upgrade ISO is detected."
                                    "Please, finish the current upgrade before"
                                    " start the new one")

        self._source_version = repo.source_version
        logger.info("SW upgrade ISO struction version is "
                    f"'{self._source_version.value}'")

        logger.info(f"Validating upgrade repo: release '{REPO_CANDIDATE_NAME}'"
                    f", source {repo.source}")

        candidate_repo = inputs.SWUpgradeRepo(
            repo.source,
            REPO_CANDIDATE_NAME,
            source_version=self._source_version.value
        )

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

            cortx_release = CortxRelease(REPO_CANDIDATE_NAME)
            metadata = cortx_release.metadata

            repo.metadata = metadata
            logger.debug(f"Resolved metadata {metadata}")

            try:
                # TODO here cortx_release.version returns 'candidate',
                #      it doesn't match metadata version info,
                #      might be a case for improvement
                release = cortx_release.release_info.version
            except KeyError:
                raise SWUpdateRepoSourceError(
                    str(repo.source),
                    f"No release data found in '{RELEASE_INFO_FILE}'"
                )

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
        if repo.source_version == ISOVersion.VERSION1:
            iso_mount_dir = repo.target_build / repo.release
            python_index_path = iso_mount_dir / CORTX_PYTHON_ISO_DIR
        else:
            iso_mount_dir = repo.target_build / repo.release
            python_index_path = (iso_mount_dir / ISOVer2.SW /
                                 ISOVer2.EXTERNAL / ISOVer2.PYTHON)

        if (
            python_index_path.exists()
            and any(
                p for p in python_index_path.iterdir() if p.is_dir()
            )
        ):
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
        # TODO: EOS-20669: what repo would exist permanently?
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

    def get_packages_version(self, release: str) -> dict:
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
        if self._source_version == ISOVersion.VERSION1:
            repo_name = CORTX_ISO_DIR
        elif self._source_version == ISOVersion.VERSION2:
            repo_name = UpgradeReposVer2.CORTX.value
        else:
            raise ValueError(f"Unsupported source version: "
                             f"{self._source_version}")

        repo = f"sw_upgrade_{repo_name}_{release}"

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
