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
from abc import abstractmethod, ABC
from hmac import compare_digest
from pathlib import Path
from typing import Dict, Callable, Optional, Union, Type

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from provisioner import utils
from provisioner.salt import local_minion_id, cmd_run
from provisioner.config import ContentType, HashType, SWUpgradeInfoFields
from provisioner.vendor import attr
from provisioner.errors import ValidationError

logger = logging.getLogger(__name__)


ARMOR_HEADER = "-----BEGIN PGP PUBLIC KEY BLOCK-----"
ARMOR_TAIL = "-----END PGP PUBLIC KEY BLOCK-----"


class PathValidator(ABC):

    """Abstract Path Validator class defines the interface for inheritance."""

    @abstractmethod
    def validate(self, path: Path):
        """
        Abstract validation method of Validator.

        Parameters
        ----------
        path: Path
            path for file validation


        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        pass

    def __call__(self, *args, **kwargs):
        """
        Call-wrapper over self.validate method. It adds function-like behavior
        for all class instances.

        Parameters
        ----------
        args:
            tuple of all positional arguments
        kwargs:
            dict with all keyword arguments

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        self.validate(*args, **kwargs)


@attr.s(auto_attribs=True)
class FileValidator(PathValidator):

    """
    Class for file validation.

    Attributes
    ----------
    required: bool
        if True validation raises an Exception if the file doesn't exist
    content_validator: Optional[Callable[[Path], None]]
        callable object for file content validation.

        Should raise the `ValidationError` exception if file content validation
        is failed

    Notes
    -----
    TBD: other possible parameters
        permissions: int/str
            requested file permissions
        owner: str
            requested file owner
        group: str
            requested file group
        is_symlink: bool
            defines if file should be a symlink

    At initialization time `attr.s` is responsible for `_required`
    and `_content_validator` attributes validation.
    """

    required: bool = attr.ib(
        validator=attr.validators.instance_of(bool),
        default=False
    )
    content_validator: Optional[Callable[[Path], None]] = attr.ib(
        init=False,
        validator=attr.validators.optional(attr.validators.is_callable()),
        default=None,
    )

    def validate(self, path: Path):
        """
        Validate the file by a given path.

        Parameters
        ----------
        path: Path
            path for file validation

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.

        """
        logger.debug(f"Start '{path}' file validation")

        if not path.exists():
            if self.required:
                raise ValidationError(reason=f"File '{path}' should exist.")
            return

        logger.debug(f"File '{path}' exists.")

        if not path.is_file():
            raise ValidationError(reason=f"'{path}' is not a regular file.")

        if self.content_validator:
            # Should raise an Exception if validation fails
            self.content_validator(path)  # pylint: disable=not-callable


@attr.s(auto_attribs=True)
class DirValidator(PathValidator):

    """
    Class for catalog validation.

    Attributes
    ----------
    files_scheme: Optional[Dict]
        Nested catalog structure for the validation path

    required: bool
        if True validation raises an Exception if the directory
        doesn't exist

    empty: bool
        If False validation raises an Exception if the directory is empty

    Notes
    -----
    TBD: other possible parameters
    permissions: int/str
        requested directory permissions
    owner: str
        requested directory owner
    group: str
        requested directory group

    At initialization time `attr.s` is responsible for `_file_scheme`
    validation and converting keys of file scheme from string to `Path`
    instance.
    """

    files_scheme: Optional[Dict] = attr.ib(
        validator=attr.validators.optional(
            attr.validators.deep_mapping(
                key_validator=attr.validators.instance_of((str, Path)),
                value_validator=attr.validators.instance_of(PathValidator),
                mapping_validator=attr.validators.instance_of(dict)
            )
        ),
        converter=utils.converter_file_scheme_key,
        default=None,
    )
    required: bool = attr.ib(
        validator=attr.validators.instance_of(bool),
        default=False
    )
    empty: bool = attr.ib(
        validator=attr.validators.instance_of(bool),
        default=False
    )

    def validate(self, path: Path):
        """
        Validate the directory by a given path.

        Parameters
        ----------
        path: Path
            path for file validation

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        logger.debug(f"Start '{path}' directory validation")

        if not path.exists():
            if self.required:
                raise ValidationError(reason=f"File '{path}' should exist.")
            return

        logger.debug(f"Directory '{path}' exists.")

        if not path.is_dir():
            raise ValidationError(reason=f"'{path}' is not a directory")

        if self.files_scheme:
            if self.empty and not any(path.iterdir()):
                return
            for sub_path, validator in self.files_scheme.items():
                validator.validate(path / sub_path)


@attr.s(auto_attribs=True)
class FileSchemeValidator(PathValidator):

    """
    Scheme Validator for files and directories.

    Attributes
    ----------
    scheme: Optional[Dict]
        dictionary with files scheme

    Notes
    -----
    At initialization time `attr.s` is responsible for `_scheme` validation
    and converting keys of file scheme from string to `Path` instance.
    """

    scheme: Optional[Dict] = attr.ib(
        validator=attr.validators.optional(
            attr.validators.deep_mapping(
                key_validator=attr.validators.instance_of((str, Path)),
                value_validator=attr.validators.instance_of(PathValidator),
                mapping_validator=attr.validators.instance_of(dict)
            )
        ),
        converter=utils.converter_file_scheme_key,
        default=None
    )

    def validate(self, path: Path):
        """
        Validate the catalog structure against validation scheme for given
        path

        Parameters
        ----------
        path: Path
            path for catalog scheme validation

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        for sub_path, validator in self.scheme.items():
            validator.validate(path / sub_path)


class YumRepoDataValidator(DirValidator):

    """Special alias for yum repo data validation."""

    def __init__(self):
        super().__init__({Path("repomd.xml"): FileValidator(required=True)},
                         required=True)


@attr.s
class HashSumValidator(FileValidator):

    """
    Validator of hash-sum for the provided file and expected hash-sum for this
    file.

    Attributes
    ----------
    hash_sum: Union[str, bytes, bytearray]
        Hexadecimal string or byte-array object with expected hash-sum value
        of validated file.
    hash_type: HashType
        Type of hash sum. See `Hashtype` for more information

    """
    hash_sum: Union[str, bytes, bytearray] = attr.ib(
        validator=attr.validators.instance_of((str, bytes, bytearray)),
        converter=lambda x: bytes.fromhex(x) if isinstance(x, str) else x,
        default=None
    )
    hash_type: HashType = attr.ib(
        validator=attr.validators.in_(HashType),
        default=HashType.MD5,
        converter=lambda x: HashType.MD5 if x is None else HashType(x)
    )

    def validate(self, path: Path):
        """
        Validates if hash-sum of the file provided by `path` matches
        the attribute value of `_hash_sum`.

        Parameters
        ----------
        path: Path
            path to the file which hash-sum will be validated

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        super().validate(path)

        hash_obj = utils.calc_hash(path, self.hash_type)

        # hash_obj here is an object returned by `hashlib`
        # python istandard library module so we compare against
        # one provided by a caller
        if not compare_digest(hash_obj.digest(), self.hash_sum):
            raise ValidationError(
                    f"Hash sum of file '{path}': '{hash_obj.hexdigest()}' "
                    f"mismatches the provided one '{self.hash_sum.hex()}'")


@attr.s(auto_attribs=True)
class FileContentScheme:

    """
    Abstract file scheme class.

    It can be used to define an abstract interface if necessary.
    Also it is useful to have the parent class for all file schemes inherited
    from this one for comparison using `isinstance`, `type` and for `attr`
    module.

    Attributes
    ----------
    _unexpected_attributes: dict
        Stores all attribute values that were not listed
        in the class definition.

        Note: This attribute will be useful in the implementation of logic
        if we need to validate that some attributes should not be listed
        in the data scheme.
    """

    def set_unexpected_attributes(self, args: dict):
        self._unexpected_attrs = args

    def get_unexpected_attributes(self):
        return getattr(self, "_unexpected_attrs", None)

    _unexpected_attributes = property(get_unexpected_attributes,
                                      set_unexpected_attributes)

    @classmethod
    def from_args(cls, data: Union[list, dict]):
        unexpected_attrs = dict()
        if isinstance(data, dict):
            # TODO: it is good to make copy of input data parameter
            for _attr in (data.keys() - set(a for a in attr.fields_dict(cls))):
                # NOTE: Remove unexpected attributes from initialization `data`
                #  dictionary
                unexpected_attrs[_attr] = data.pop(_attr)

            # If some attributes are missed in `data`, the `attr` module is
            #  responsible for that validation
            obj = cls(**data)
            obj._unexpected_attributes = unexpected_attrs
            return obj
        elif isinstance(data, list):
            obj = cls(*data)
            obj._unexpected_attributes = unexpected_attrs
            return obj
        else:
            raise ValidationError(
                f"Unexpected content type: '{type(data)}'"
            )


@attr.s(auto_attribs=True)
class ReleaseInfoCommonContentScheme(FileContentScheme):

    """
    Common Cortx release info files content scheme.

    Attributes
    ----------
    NAME: str
        Name of SW upgrade repository. It is the `NAME` field of `RELEASE.INFO`
        file
    RELEASE: Optional[str]
        Release of SW upgrade repository. Can be absent. It is the `RELEASE`
        field of `RELEASE.INFO` file
    VERSION: str
        Version number of SW upgrade repository. It is the `VERSION` field of
        `RELEASE.INFO` file
    BUILD: str
        Build number of SW upgrade repository. It is the `BUILD` field of
        `RELEASE.INFO` file
    OS: str
        OS version for which this SW upgrade repo is intended.
        It is the `OS` field of `RELEASE.INFO` file
    """

    NAME: str = attr.ib(
        validator=attr.validators.instance_of(str)
    )
    VERSION: str = attr.ib(
        # regex is based on the current representation of `RELEASE` field
        # number. It is 3 numbers divided by dots "."
        validator=attr.validators.matches_re(r"^[0-9]+\.[0-9]+\.[0-9]+$"),
        converter=str
    )
    BUILD: str = attr.ib(
        # regex is based on the current representation of `BUILD` number.
        # It is 1 or more numbers
        validator=attr.validators.matches_re(r"^[0-9]+$"),
        converter=str
    )
    OS: str = attr.ib(
        validator=attr.validators.instance_of(str)
    )
    RELEASE: Optional[str] = attr.ib(
        # TODO: when the `RELEASE` field will be introduced need to use here
        #  a proper regex validation
        validator=attr.validators.optional(
            attr.validators.instance_of(str)
        ),
        default=None
    )


@attr.s(auto_attribs=True)
class ReleaseInfoContentScheme(ReleaseInfoCommonContentScheme):

    """
    RELEASE.INFO file content scheme.

    This class is used for `RELEASE.INFO` file content validation.

    Attributes
    ----------
    COMPONENTS: list
        List of RPMs provided by this SW upgrade repository.
        It is the `COMPONENTS` field of `RELEASE.INFO` file
    """

    COMPONENTS: list = attr.ib(
        validator=attr.validators.instance_of(list),
        kw_only=True
    )


@attr.s(auto_attribs=True)
class ThirdPartyReleaseInfoContentScheme(ReleaseInfoCommonContentScheme):

    """
    RELEASE.INFO file content scheme.

    This class is used for `RELEASE.INFO` file content validation.

    Attributes
    ----------
    NAME: str
        Name of SW upgrade repository. It is the `NAME` field of `RELEASE.INFO`
        file
    RELEASE: Optional[str]
        Release of SW upgrade repository. Can be absent. It is the `RELEASE`
        field of `RELEASE.INFO` file
    VERSION: str
        Version number of SW upgrade repository. It is the `VERSION` field of
        `RELEASE.INFO` file
    BUILD: str
        Build number of SW upgrade repository. It is the `BUILD` field of
        `RELEASE.INFO` file
    OS: str
        OS version for which this SW upgrade repo is intended.
        It is the `OS` field of `RELEASE.INFO` file
    COMPONENTS: list
        List of RPMs provided by this SW upgrade repository.
        It is the `COMPONENTS` field of `RELEASE.INFO` file
    """

    # TODO validator (current format looks odd: os-version-build)
    THIRD_PARTY_VERSION: str = attr.ib(
        converter=str, kw_only=True
    )
    THIRD_PARTY_COMPONENTS: dict = attr.ib(
        validator=attr.validators.instance_of(dict),
        kw_only=True
    )


@attr.s(auto_attribs=True)
class ContentFileValidator(PathValidator):

    """
    Class implements the basic logic of file content validation.

    Attributes
    ----------
    scheme: Type[FileContentScheme]
        File content scheme for validation.

    content_type: ContentType
        Content type of the file. `ContentType.YAML` is default value

    """

    scheme: Type[FileContentScheme] = attr.ib(
        validator=utils.validator__subclass_of(FileContentScheme)
    )
    content_type: ContentType = attr.ib(
        validator=attr.validators.in_(ContentType),
        default=ContentType.YAML
    )

    _CONTENT_LOADER = {
        ContentType.YAML: utils.load_yaml,
        ContentType.JSON: utils.load_json,
    }

    def validate(self, path: Path):
        """
        Validates the file content of the provided `path`.

        Parameters
        ----------
        path: Path
            File path for content validation

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        logging.debug(f"File content type: '{self.content_type}'")
        try:
            content = self._CONTENT_LOADER[self.content_type](path)
        except Exception as e:
            raise ValidationError(
                f"Failed to load the content of {path}: {e}"
            ) from e

        logging.debug(f"File content: '{content}'")
        try:
            self.scheme.from_args(content)
        except TypeError as e:
            raise ValidationError(
                f"File content validation is failed for {path}: {e}"
            ) from e
        else:
            logging.info(f"File content validation is succeeded for '{path}'")


@attr.s(auto_attribs=True)
class ReleaseInfoValidatorBase(FileValidator):

    """
    Special alias for release info file validators.

    Attributes
    ----------
    required: bool
        if `True` validation raises an Exception if the file doesn't exist.
        `True` by default
    content_type: ContentType
        Content type of the `RELEASE.INFO` file.
        `ContentType.YAML` is default value
    """

    required: bool = attr.ib(
        validator=attr.validators.instance_of(bool),
        # NOTE: it is a difference in comparison of `FileValidator`
        default=True
    )
    content_type: ContentType = attr.ib(
        validator=attr.validators.in_(ContentType),
        default=ContentType.YAML
    )

    def __attrs_post_init__(self):
        self.content_validator = ContentFileValidator(
                scheme=ReleaseInfoContentScheme,
                content_type=self.content_type)


@attr.s(auto_attribs=True)
class AuthenticityValidator(PathValidator):
    """
    Class for file authenticity validation using GPG tool

    Attributes
    ----------
    signature: Union[str, Path]
        if True validation raises an Exception if the file doesn't exist
    gpg_public_key: Optional[Union[str, Path]]
        callable object for file content validation.

    """

    signature: Union[str, Path] = attr.ib(
        validator=utils.validator_path_exists,
        converter=utils.converter_path_resolved
    )
    gpg_public_key: Optional[Union[str, Path]] = attr.ib(
        validator=attr.validators.optional(utils.validator_path_exists),
        converter=utils.converter_path_resolved,
        default=None
    )

    @staticmethod
    def _convert_key_to_open_pgp_format(pub_key_path: Path) -> Path:
        """
        Check if GPG Public key in ASCII Armor format. If so format it to
        OpenPGP format.

        Parameters
        ----------
        pub_key_path: Path
            Path to GPG public key

        Returns
        -------
        Path:
            path to the file with GPG public key in OpenPGP format

        """
        # NOTE: for the ASCII Armor format, please, refer to RFC4880
        #  https://datatracker.ietf.org/doc/html/rfc4880#section-6.2

        # NOTE: return given path itself if it is in OpenPGP format already
        res = pub_key_path
        with open(pub_key_path, "rb") as fh:
            # NOTE: read file as binary file since OpenPGP is binary format
            content = fh.readlines()
            armor_header = content[0]
            armor_tail = content[-1]

        # NOTE: we check that the armor header and armor tail in binary
        #  representation exist in the first and the last line of
        #  the pub key file.
        if (ARMOR_HEADER.encode() in armor_header
                and ARMOR_TAIL.encode() in armor_tail):
            # NOTE: it means that provided public key is in ASCII Armor format
            cmd = f"gpg --yes --dearmor {pub_key_path.resolve()}"
            try:
                # NOTE: by default gpg tool converts the given file to the file
                #  with the same name + '.gpg' extension at the end.
                #  Directory is the same
                cmd_run(cmd, targets=local_minion_id())
            except Exception as e:
                logger.error("Can't convert ASCII Armor GPG public key "
                             f"'{pub_key_path.resolve()}'"
                             f"to OpenPGP format: '{e}'")
                raise ValidationError(
                    f'Public key conversion error: "{e}"') from e
            else:
                # NOTE: because .with_suffix method replaces the last suffix
                suffix = pub_key_path.suffix + ".gpg"
                res = pub_key_path.with_suffix(suffix)

        return res

    def validate(self, path: Path) -> str:
        """
        Validate the file by a given path has a correct signature

        Parameters
        ----------
        path: Path
            path for the file authenticity validation

        Returns
        -------
        str:
            Comment message about GPG verification

        Raises
        ------
        ValidationError
            If validation is failed.

        """
        logger.debug(f"Start '{path}' file authenticity validation")

        if self.gpg_public_key is not None:
            # NOTE: for validation signature with the custom GPG pub key
            #  it is required to use pub key in OpenPGP format, not in
            #  ASCII Armor format (--armor option of gpg tool)
            open_pgp_key = self._convert_key_to_open_pgp_format(
                self.gpg_public_key
            )
            cmd = (f"gpg --no-default-keyring --keyring {open_pgp_key} "
                   f"--verify {self.signature} {path}")
        else:
            cmd = f"gpg --verify {self.signature} {path}"

        try:
            res = cmd_run(cmd, targets=local_minion_id())
        except Exception as e:
            logger.debug(f'Authenticity check is failed: "{e}"')
            raise ValidationError(
                f'Authenticity check is failed: "{e}"') from e

        return res


class ReleaseInfoValidator(ReleaseInfoValidatorBase):

    """
    Special alias for `RELEASE.INFO` file validator.
    """

    def __attrs_post_init__(self):
        self.content_validator = ContentFileValidator(
                scheme=ReleaseInfoContentScheme,
                content_type=self.content_type)


@attr.s(auto_attribs=True)
class ThirdPartyReleaseInfoValidator(ReleaseInfoValidatorBase):

    """
    Special alias for `THIRD_PARTY_RELEASE.INFO` file validator.
    """

    def __attrs_post_init__(self):
        self.content_validator = ContentFileValidator(
                scheme=ThirdPartyReleaseInfoContentScheme,
                content_type=self.content_type)


@attr.s(auto_attribs=True)
class CompatibilityValidator:

    """
    Validator that checks if all SW upgrade packages are compatible with
    installed ones.
    """

    def validate(self, iso_info):
        """

        Parameters
        ----------
        iso_info: CortxISOInfo
            CortxISOInfo instance with all necessary information about
            SW upgrade ISO

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        packages = list(iso_info.packages.keys())

        # NOTE: the first line of `yum -q list installed` command is
        #  'Installed Packages' skip it via `tail -n +2`
        cmd = (f"yum -q list installed {' '.join(packages)} 2>/dev/null |"
               f" tail -n +2 | awk '{{print $1\" \"$2}}'")

        try:
            res = cmd_run(cmd, targets=local_minion_id())
        except Exception as e:
            logger.debug(f'Package compatibility check is failed: "{e}"')
            raise ValidationError(
                f'Package compatibility check is failed: "{e}"') from e

        res = res[local_minion_id()].strip()

        if res:
            logger.debug(f"List of installed CORTX packages: {res}")
        else:
            logger.warning(f"There are no installed CORTX packages")
            return  # Nothing to validate since there are not CORTX packages

        res = res.split('\n')

        packages = dict()
        for pkg in res:
            # Aggregate version information of installed CORTX packages
            pkg_name, pkg_version = pkg.split(" ")
            # remove architecture post-fix from the package name
            pkg_name = pkg_name.split(".")[0]
            packages[pkg_name] = pkg_version

        error_msg = list()
        for pkg in iso_info.packages:
            if (SWUpgradeInfoFields.VERSION_COMPATIBILITY.value
                    in iso_info.packages[pkg]):
                compatibility = iso_info.packages[pkg][
                    SWUpgradeInfoFields.VERSION_COMPATIBILITY.value]

                installed_ver = packages.get(pkg, None)
                if installed_ver is None:
                    msg = f"CORTX package {pkg} is not installed"
                    logger.error(msg)
                    error_msg.append(msg)
                    continue

                if Version(installed_ver) in SpecifierSet(compatibility):
                    logger.info(f"CORTX package {pkg} satisfies the constraint"
                                f" version '{compatibility}'")
                else:
                    msg = (f"CORTX package {pkg} does not satisfies the "
                           f"constraint version '{compatibility}'")
                    logger.error(msg)
                    error_msg.append(msg)

        if error_msg:
            raise ValidationError("During validation some compatibility "
                                  f"errors were found: {'/n'.join(error_msg)}")
