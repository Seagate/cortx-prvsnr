import logging
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Dict, Callable

from ... import utils

from ...vendor import attr
from ...errors import ValidationError

logger = logging.getLogger(__name__)


class Validator(ABC):

    """Abstract Validator class defines the interface for inheritance."""

    @abstractmethod
    def validate(self, *args, **kwargs):
        """
        Abstract validation method of Validator.

        Parameters
        ----------
        args
            list of positional arguments
        kwargs
            keyword-only arguments

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
class FileValidator(Validator):

    """
    Class for file validation.

    Attributes
    ----------
    _required: bool
        if True validation raises an Exception if the file doesn't exist
    _content_validator: Callable[[Path], None]
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
        validator=attr.validators.optional(attr.validators.instance_of(bool)),
        default=False
    )
    _content_validator: Callable[[Path], None] = attr.ib(
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

        if self._content_validator and callable(self._content_validator):
            # Should raise an Exception if validation fails
            self._content_validator(path)


@attr.s(auto_attribs=True)
class DirValidator(Validator):

    """
    Class for catalog validation.

    Attributes
    ----------
    _files_scheme: Dict
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

    _files_scheme: Dict = attr.ib(
        validator=attr.validators.optional(
            attr.validators.deep_mapping(
                key_validator=attr.validators.instance_of((str, Path)),
                # we can't refer to DirValidator here.
                # Replace it to parent class
                value_validator=attr.validators.instance_of(Validator),
                mapping_validator=attr.validators.instance_of(dict)
            )
        ),
        converter=utils.file_scheme_key_converter,
        default=None,
    )
    _required: bool = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(bool)),
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

        if self._files_scheme and isinstance(self._files_scheme, dict):
            for sub_path, validator in self._files_scheme.items():
                validator.validate(path / sub_path)


@attr.s(auto_attribs=True)
class FileSchemeValidator(Validator):

    """
    Scheme Validator for files and directories.

    Attributes
    ----------
    _scheme: Dict
        dictionary with files scheme

    Notes
    -----
    At initialization time `attr.s` is responsible for `_scheme` validation
    and converting keys of file scheme from string to `Path` instance.
    """

    _scheme: Dict = attr.ib(
        validator=attr.validators.optional(
            attr.validators.deep_mapping(
                key_validator=attr.validators.instance_of((str, Path)),
                value_validator=attr.validators.instance_of((FileValidator,
                                                             DirValidator)),
                mapping_validator=attr.validators.instance_of(dict)
            )
        ),
        converter=utils.file_scheme_key_converter,
        default=None
    )

    def validate(self, base_path: Path):
        """
        Validate the catalog structure against validation scheme for given
        path

        Parameters
        ----------
        base_path: Path
            path for catalog scheme validation

        Returns
        -------
        None

        Raises
        ------
        ValidationError
            If validation is failed.
        """
        for path, validator in self._scheme.items():
            validator.validate(base_path / path)
