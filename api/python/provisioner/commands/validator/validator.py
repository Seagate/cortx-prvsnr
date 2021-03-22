import hashlib
import logging
from abc import abstractmethod, ABC
from hmac import compare_digest
from pathlib import Path
from typing import Dict, Callable, Optional, Union

from provisioner.config import HashType

from ... import utils

from ...vendor import attr
from ...errors import ValidationError

logger = logging.getLogger(__name__)


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


@attr.s(auto_attribs=True)
class FileValidator(PathValidator):

    """
    Class for file validation.

    Attributes
    ----------
    _required: bool
        if True validation raises an Exception if the file doesn't exist
    _content_validator: Optional[Callable[[Path], None]]
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

    _required: bool = attr.ib(
        validator=attr.validators.instance_of(bool),
        default=False
    )
    _content_validator: Optional[Callable[[Path], None]] = attr.ib(
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
            if self._required:
                raise ValidationError(reason=f"File '{path}' should exist.")
            return

        logger.debug(f"File '{path}' exists.")

        if not path.is_file():
            raise ValidationError(reason=f"'{path}' is not a regular file.")

        if self._content_validator:
            # Should raise an Exception if validation fails
            self._content_validator(path)  # pylint: disable=not-callable


@attr.s(auto_attribs=True)
class DirValidator(PathValidator):

    """
    Class for catalog validation.

    Attributes
    ----------
    _files_scheme: Optional[Dict]
        Nested catalog structure for the validation path

    _required: bool
        if True validation raises an Exception if the directory
        doesn't exist

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

    _files_scheme: Optional[Dict] = attr.ib(
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
    _required: bool = attr.ib(
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
            if self._required:
                raise ValidationError(reason=f"File '{path}' should exist.")
            return

        logger.debug(f"Directory '{path}' exists.")

        if not path.is_dir():
            raise ValidationError(reason=f"'{path}' is not a directory")

        if self._files_scheme:
            for sub_path, validator in self._files_scheme.items():
                validator.validate(path / sub_path)


@attr.s(auto_attribs=True)
class FileSchemeValidator(PathValidator):

    """
    Scheme Validator for files and directories.

    Attributes
    ----------
    _scheme: Optional[Dict]
        dictionary with files scheme

    Notes
    -----
    At initialization time `attr.s` is responsible for `_scheme` validation
    and converting keys of file scheme from string to `Path` instance.
    """

    _scheme: Optional[Dict] = attr.ib(
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
        for sub_path, validator in self._scheme.items():
            validator.validate(path / sub_path)


class YumRepoDataValidator(DirValidator):

    """Special alias for yum repo data validation."""

    def __init__(self):
        super().__init__({Path("repomd.xml"): FileValidator(required=True)},
                         required=True)


@attr.s
class HashSumValidator(PathValidator):

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
    _hash_sum: Union[str, bytes, bytearray] = attr.ib(
        validator=attr.validators.instance_of((str, bytes, bytearray))
    )
    _hash_type: HashType = attr.ib(
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
        file_validator = FileValidator(required=True)
        file_validator.validate(path)

        if self._hash_type.value not in hashlib.algorithms_available:
            raise ValidationError(f"Hash type '{self._hash_type.value}' is not"
                                  "supported by Python's `hashlib` module.")

        hash_method = getattr(hashlib, self._hash_type.value)()

        with open(path, 'rb') as fh:
            while True:
                data = fh.read(4096)
                if not data:
                    break
                hash_method.update(data)

        if isinstance(self._hash_sum, str):
            self._hash_sum = bytes.fromhex(self._hash_sum)

        if not compare_digest(hash_method.digest(), self._hash_sum):
            raise ValidationError(
                    f"Hash sum of file '{path}': '{hash_method.hexdigest()}' "
                    f"mismatches the provided one '{self._hash_sum.hex()}'")
