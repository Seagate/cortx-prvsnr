import logging
from abc import abstractmethod
from pathlib import Path
from typing import Dict, Callable

from ...errors import ValidationError

logger = logging.getLogger(__name__)


class SchemeValidator:

    """Base Scheme Validator. It defines the interface for child classes."""

    def __init__(self):
        pass

    @abstractmethod
    def validate(self, *args, **kwargs):
        """
        Abstract Scheme validation method.

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


class Validator:

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


class FileValidator(Validator):

    """Class for file validation."""

    def __init__(self, *, required: bool = False,
                 content_validator: Callable[[Path], None] = None):
        """
        File validator initialization method

        Parameters
        ----------
        required: bool
            if True validation raises an Exception if the file doesn't exist
        content_validator: Callable[[Path], None]
            callable object for file content validation

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
        """
        self._required = required
        self._content_validator = content_validator

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


class DirValidator:

    """Class for catalog validation."""

    def __init__(self, files_scheme: Dict = None, required: bool = False):
        """
        Catalog validator initialization method.

        Parameters
        ----------
        files_scheme: Dict
            Nested catalog structure for the validation path

        required: bool
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
        """
        self._files_scheme = files_scheme
        self._required = required

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
                if isinstance(sub_path, str):
                    sub_path = Path(sub_path)
                elif not isinstance(sub_path, Path):
                    raise ValueError("Keys of the nested catalog file scheme "
                                     "should be a string or instantiated from "
                                     "'Path' class")
                validator.validate(path / sub_path)


class FileSchemeValidator(SchemeValidator):

    """Scheme Validator for files and directories."""

    def __init__(self, file_scheme: Dict):
        """
        Initialization method.

        Parameters
        ----------
        file_scheme: Dict
            dictionary with file scheme
        """
        super().__init__()

        self._scheme = file_scheme

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
            if isinstance(base_path, str):
                base_path = Path(base_path)
            elif not isinstance(base_path, Path):
                raise ValueError("Keys of the files scheme should be a strings"
                                 " or instantiated from 'Path' class")
            validator.validate(base_path / path)
