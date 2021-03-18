import logging
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Dict, Callable, Optional, Type

from ... import utils
from ...config import ContentType

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


class FileScheme(ABC):

    """
    Abstract file scheme class.

    It can be used to define an abstract interface if necessary.
    Also it is useful to have the parent class for all file schemes inherited
    from this one for comparison using `isinstance`, `type` and for `attr`
    module.
    """
    pass


@attr.s
class ReleaseInfoScheme(FileScheme):

    """
    RELEASE.INFO file content scheme.

    This class is used for `RELEASE.INFO` file content validation.

    Attributes
    ----------
    name: str
        Name of SW upgrade repository. It is the `NAME` field of `RELEASE.INFO`
        file
    release: Optional[str]
        Release of SW upgrade repository. Can be absent. It is the `RELEASE`
        field of `RELEASE.INFO` file
    version: str
        Version number of SW upgrade repository. It is the `VERSION` field of
        `RELEASE.INFO` file
    build: str
        Build number of SW upgrade repository. It is the `BUILD` field of
        `RELEASE.INFO` file
    os: str
        OS version for which this SW upgrade repo is intended.
        It is the `OS` field of `RELEASE.INFO` file
    components: list
        List of RPMs provided by this SW upgrade repository.
        It is the `COMPONENTS` field of `RELEASE.INFO` file
    """

    name: str = attr.ib(
        validator=attr.validators.instance_of(str)
    )
    release: Optional[str] = attr.ib(
        # TODO: when we the `RELEASE` will be introduce need to use here
        #  a proper regex validation
        validator=attr.validators.optional(
            attr.validators.instance_of(str)
        ),
        default=None
    )
    version: str = attr.ib(
        # regex is based on the current representation of `RELEASE` field
        # number. It is 3 numbers divided by dots "."
        validator=attr.validators.matches_re("^[0-9]+\.[0-9]+\.[0-9]+$")
    )
    build: str = attr.ib(
        # regex is based on the current representation of `BUILD` number.
        # It is 1 or more numbers
        validator=attr.validators.matches_re("^[0-9]+$")
    )
    os: str = attr.ib(
        validator=attr.validators.instance_of(str)
    )
    components: list = attr.ib(
        validator=attr.validators.instance_of(list)
    )


@attr.s
class ContentFileValidator(PathValidator):

    """
    Class implements the basic logic of file content validation.

    Attributes
    ----------
    scheme: ReleaseInfoScheme
        File content scheme for validation.

    content_type: ContentType
        Content type of the file. `ContentType.YAML` is default value

    """

    _scheme: Type[ReleaseInfoScheme] = attr.ib(
        validator=attr.validators.instance_of(FileScheme)
    )
    _content_type: ContentType = attr.ib(
        validator=attr.validators.in_(ContentType),
        default=ContentType.YAML
    )

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
        try:
            logging.debug(f"File content type: '{self._content_type}'")
            if self._content_type == ContentType.YAML:
                content = utils.load_yaml(path)
            elif self._content_type == ContentType.JSON:
                content = utils.load_json(path)
            else:
                raise ValidationError(
                            f"File content type '{self._content_type}'"
                            " is not supported")
        except Exception as e:
            raise ValidationError(
                            f"File content validation is failed: {e}") from e

        logging.debug(f"File content: '{content}'")
        try:
            if isinstance(content, dict):
                content_model = self._scheme(**content)
            elif isinstance(content, list):
                content_model = self._scheme(*content)
            else:
                raise ValidationError("Unexpected top-level content type: "
                                      f"'{type(content)}'")
        except TypeError as e:
            raise ValidationError(f"File content validation is failed: {e}")
        else:
            logging.info(f"File content validation is succeeded for '{path}'")

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


class ReleaseInfoValidator(FileValidator):

    """
    Special alias for `RELEASE.INFO` file validator.

    Attributes
    ----------
    _required: bool
        if `True` validation raises an Exception if the file doesn't exist.
        `True` by default
    _content_type: ContentType
        Content type of the `RELEASE.INFO` file.
        `ContentType.YAML` is default value
    """

    _required: bool = attr.ib(
        validator=attr.validators.instance_of(bool),
        # NOTE: it is a difference in comparison of `FileValidator`
        default=True
    )
    _content_type: ContentType = attr.ib(
        validator=attr.validators.in_(ContentType),
        default=ContentType.YAML
    )

    def __attrs_post_init__(self):
        self._content_validator = ContentFileValidator(
                scheme=ReleaseInfoScheme,
                content_type=self._content_type)
