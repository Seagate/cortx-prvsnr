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

from typing import (
    Tuple,
    Union,
    Optional,
    List,
    Type,
    Any,
    Callable,
    Iterator,
    BinaryIO
)
import hashlib
import configparser
import json
import logging
import random
import subprocess
import time
import string
from shlex import quote
from pathlib import Path, PosixPath
import yaml
from packaging.version import Version

from . import config

from .errors import (
    BadPillarDataError, SubprocessCmdError, NoMoreTriesError
)

from .vendor import attr

logger = logging.getLogger(__name__)


# https://www.gnu.org/software/tar/
TAR_VER_WITH_SORT_OPT = '1.28'


HashInfo = attr.make_class(
    "HashInfo",
    {
        'hash_type': attr.ib(default=None),
        'hash_sum': attr.ib(
            validator=attr.validators.optional(
                attr.validators.instance_of((bytes, bytearray))),
            default=None,
            converter=lambda x: bytes.fromhex(x)
            if isinstance(x, str) else x),
        'filename': attr.ib(default=None)
    })


DictLeaf = attr.make_class(
    "DictLeaf", ('key', 'value', 'parent', 'keypath')
)


def iterate_dict(d, path: Path = None, filter_f=None) -> Iterator[DictLeaf]:
    # list: considering changes in base dictionary during the iteration
    for k in list(d):
        v = d[k]
        _path = (Path(str(k)) if path is None else (path / k))
        if isinstance(v, dict) and v:
            yield from iterate_dict(v, _path, filter_f)
        else:
            leaf = DictLeaf(k, v, d, _path)
            if not filter_f or filter_f(leaf):
                yield leaf


# TODO TEST
# FIXME remove on behalf of ones from attr_gen
def validator_path(instance, attribute, value):
    if value is None:
        if attribute.default is not None:
            raise ValueError(f"{attribute.name} should be defined")
    elif not isinstance(value, Path):
        raise TypeError(f"{attribute.name} should be a Path")


def validator_path_exists(instance, attribute, value):
    validator_path(instance, attribute, value)

    if value and not value.exists():
        raise ValueError(f"Path {value} doesn't exist")


def validator_dir_exists(instance, attribute, value):
    validator_path(instance, attribute, value)

    if not value.is_dir():
        raise ValueError(f"Path {value} is not a directory")


def validator_file_exists(instance, attribute, value):
    validator_path(instance, attribute, value)

    if not value.is_file():
        raise ValueError(f"Path {value} is not a file")


def converter_path(value):
    return value if value is None else Path(str(value))


def converter_file_scheme_key(value: dict):
    """
    Convert incoming dict with file scheme to new one where keys are `Path`
    instances

    Parameters
    ----------
    value: dict
        a given file scheme which represents some catalog structure

    Returns
    -------
    dict
        new dictionary object where keys are `Path` instances
    """
    return value if value is None else {converter_path(k): v for k, v in
                                        value.items()}


def converter_path_resolved(value):
    return value if value is None else Path(str(value)).resolve()


def validator__subclass_of(
        subclass: Union[Type[Any], Tuple[Type[Any], ...]]) -> Callable:
    """
    Custom subclass validator extends the base `attrs.validator` functionality.
    This validation function allows to check if attribute value is subclass
    of the provided `subclass` parameter

    Parameters
    ----------
    subclass: Union[Type[Any], Tuple[Type[Any], ...]]
        Any class name or tuple of classes

    Returns
    -------
    Callable
        subclass validation function

    """
    def validator(instance, attribute, value):
        if not issubclass(value, subclass):
            raise TypeError(
                f"'{attribute.name}' must be {subclass!r} (got {value!r} "
                f"that is a {value.__base__!r}).",
                attribute,
                subclass,
                value,
            )

    return validator


def load_yaml_str(data):
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError as exc:
        logger.exception("Failed to load pillar data")
        raise BadPillarDataError(str(exc))


def dump_yaml_str(
    data,
    width=1,
    indent=4,
    default_flow_style=False,
    canonical=False,
    **kwargs
):
    # TODO: Either check if this is the right way to accomplish this
    # Or we should work to use a add_constructor
    def posix_path_representer(dumper_obj, posix_path_obj):
        return dumper_obj.represent_scalar(
            "tag:yaml.org,2002:str",
            str(posix_path_obj)
        )
    yaml.add_representer(PosixPath, posix_path_representer)

    # return yaml.safe_dump(
    #     data,
    #     default_flow_style=default_flow_style,
    #     canonical=canonical,
    #     width=width,
    #     indent=indent,
    #     **kwargs
    # )
    return yaml.dump(
        data,
        default_flow_style=default_flow_style,
        canonical=canonical,
        width=width,
        indent=indent,
        **kwargs
    )


# TODO streamed read
def load_yaml(path):
    path = Path(str(path))
    try:
        return load_yaml_str(path.read_text())
    except yaml.YAMLError as exc:
        logger.exception("Failed to load pillar data")
        raise BadPillarDataError(str(exc))


def load_json_str(data: str):
    """
    JSON load helper. Loads JSON from a string

    Parameters
    ----------
    data: str
        JSON string to load

    Returns
    -------
    Any:
        returns JSON-deserialized object

    Raises
    ------
    JSONDecodeError
    """
    return json.loads(data)


def load_json(path: Union[Path, str]):
    """
    JSON load helper. Loads JSON from given `path`

    Parameters
    ----------
    path: Path
        Path to file with JSON content

    Returns
    -------
    Any:
        returns JSON-deserialized object

    Raises
    ------
    JSONDecodeError
    """
    return load_json_str(Path(path).read_text())


# TODO streamed write
def dump_yaml(path, data, **kwargs):
    path = Path(str(path))
    path.write_text(dump_yaml_str(data, **kwargs))


def quote_shell_cmd(cmd: List):
    return [quote(p) for p in cmd]


# TODO IMPROVE:
#   - exceptions in check callback
def ensure(  # noqa: C901 FIXME
    check_cb, tries=10, wait=1, name=None,
    expected_exc: Union[Tuple, Exception, None] = None
):
    if name is None:
        try:
            name = check_cb.__name__
        except AttributeError:
            name = str(check_cb)

    ntry = 0
    while True:
        exc = None
        ntry += 1
        logger.debug(
            'Try #{}/{} for {}'
            .format(ntry, tries, name)
        )

        try:
            if check_cb():
                return
        except Exception as _exc:
            if expected_exc and isinstance(_exc, expected_exc):
                logger.info(
                    'Try #{}/{} for {} failed: {!r}'
                    .format(ntry, tries, name, _exc)
                )
                exc = _exc
            else:
                raise

        if ntry < tries:
            time.sleep(wait)
        else:
            if exc:
                raise exc
            else:
                raise NoMoreTriesError(f'no more tries for {name}')


def run_subprocess_cmd(cmd, check=True, **kwargs):
    _kwargs = dict(
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check
    )

    _kwargs.update(kwargs)

    if not _kwargs.get('shell', False) and isinstance(cmd, str):
        cmd = cmd.split()

    try:
        # TODO IMPROVE EOS-8473 logging level
        logger.debug(f"Subprocess command {cmd}, kwargs: {_kwargs}")
        res = subprocess.run(cmd, **_kwargs)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.exception(f"Failed to run cmd '{cmd}'")
        raise SubprocessCmdError(cmd, _kwargs, exc) from exc
    else:
        logger.debug(
            f"Subprocess command {res.args} "
            f"resulted in - stdout: {res.stdout}, "
            f"returncode: {res.returncode}, stderr: {res.stderr}"
        )
        return res


def repo_tgz(
    dest: Path,
    project_path: Optional[Path] = None,
    version: str = config.REPO_VERSION_RAW,
    include_dirs: Optional[List] = None,
    exclude_dirs: Optional[List] = None
):
    if project_path is None:
        project_path = config.PROJECT_PATH

    if not project_path:
        raise ValueError('project path is not specified')

    if include_dirs is None:
        include_dirs = ['.']

    include_dirs = [str(d) for d in include_dirs]

    exclude = []
    for d in (exclude_dirs or []):
        exclude.extend(['--exclude', str(d)])

    # FIXME: version can be None
    if version and version != config.REPO_VERSION_RAW:
        # treat the version as git commit/branch/tag ...
        cmd = (
            ['git', 'archive', '--format=tar.gz', version, '-o', str(dest)] +
            include_dirs
        )
    else:
        # TODO based on some assumptions regarding tar --version output format
        tar_version = run_subprocess_cmd(
            ['tar', '--version']
        ).stdout.split()[3]

        # that makes tar to produce the same hash if no changes
        # but it works good only for --sort opt
        sort_opts = (
            ['--sort', 'name']
            if (Version(tar_version) >= Version(TAR_VER_WITH_SORT_OPT))
            else []
        )

        # do raw archive with uncommitted/untracked changes otherwise
        cmd = (
            ['tar', '-czf', str(dest)] +
            ['--exclude-vcs'] +
            ['--exclude-from', str(config.PROJECT_PATH / '.gitignore')] +
            # not available in older versions of tar also doesn't seem to work
            # in case multple targets e.g. not just '.'
            # ['--exclude-vcs-ignores'] +
            exclude +
            sort_opts +
            ['-C', str(project_path)] +
            include_dirs
        )

    run_subprocess_cmd(cmd)

    return dest


# Validates the hostname string in config.ini
# against hostname in CLI args
def node_hostname_validator(
    nodes,
    config_path
):
    node_dict = {}
    for node in nodes:
        node_dict[node.minion_id] = node.host

    logger.debug(
        "Validating list of nodes: "
        f"{yaml.dump(node_dict, default_flow_style=False)}"
    )
    logger.debug(f"Config file path: {config_path}")

    parser_obj = configparser.ConfigParser()
    parser_obj.read(config_path)

    for section in parser_obj.sections():
        if (
            "srvnode" in section and
            "srvnode_default" not in section and
            (
                node_dict[section] != parser_obj[section]["hostname"]
            )
        ):
            msg = (
                "Hostname values from config.ini and CLI did not match. "
                f"{node_dict[section]} != {parser_obj[section]['hostname']}"
            )
            raise ValueError(msg)


def generate_random_secret():
    """
    Generates a random 14 character password
    """

    special_characters = '=+-_'
    passwd_seed = (
        random.sample(string.ascii_uppercase, 4)
        + random.sample(string.digits, 3)
        + random.sample(string.ascii_lowercase, 4)
        + random.sample(special_characters, 3)
    )
    random.shuffle(passwd_seed)

    return ''.join(passwd_seed)


def load_checksum_from_str(hash_str: str) -> HashInfo:
    """
    Function helper to load hash checksum from specially constructed string.
    It parses the hash type, hash sum and file name information from
    provided string.

    Supported formats of checksum string:

    1. <hash_type>:<check_sum> <file_name>
    2. <hash_type>:<check_sum>
    3. <check_sum> <file_name>
    4. <check_sum>

    where
    <hash_type> - one of the values from `config.HashType` enumeration
    <check_sum> - hexadecimal representation of hash checksum
    <file_name> - a file name to which <hash_type> and <hash_sum> belongs to

    Parameters
    ----------
    hash_str: str
        Specially formatted string with hash data

    Returns
    -------
    HashInfo
        return `HashInfo` object-like variable with parsed information:
            <check_sum>, <hash_type>, <file_name>
        each field of this element can be `None`
    """
    hash_info = HashInfo()
    hash_info.hash_sum = hash_str.strip()
    if ":" in hash_str:
        hash_info.hash_type, hash_info.hash_sum = hash_str.split(":")

    if " " in hash_info.hash_sum:
        hash_info.hash_sum, hash_info.filename = hash_info.hash_sum.split(" ")

    hash_info.hash_type = (hash_info.hash_type
                           and config.HashType(hash_info.hash_type))

    return hash_info


def load_checksum_from_file(path: Path) -> HashInfo:
    """
    Function helper to load hash checksum from the given file. Also, it parses
    hash type of checksum if this info is available in the content.

    Supported formats of checksum file:

    1. <hash_type>:<check_sum> <file_name>
    2. <hash_type>:<check_sum>
    3. <check_sum> <file_name>
    4. <check_sum>

    where
    <hash_type> - one of the values from `config.HashType` enumeration
    <check_sum> - hexadecimal representation of hash checksum
    <file_name> - a file name to which <hash_type> and <hash_sum> belongs to

    Parameters
    ----------
    path: Path
        path to file that contains expected check-sum

    Returns
    -------
    HashInfo
        return `HashInfo` object-like variable with parsed information:
            <check_sum>, <hash_type>, <file_name>
        each field of this element can be `None`
    """
    if not path.exists():
        raise ValueError(f"File by provided path '{path}' doesn't exist.")

    with open(path, "r") as fh:
        line = fh.readline().strip()

    if not line:
        raise ValueError(f"File by provided path '{path}' is empty.")

    # NOTE: at this moment we consider that all necessary information is only
    # in first-line
    return load_checksum_from_str(line)


def calc_hash(
    data: Union[bytes, BinaryIO, Path],
    hash_type: config.HashType = config.HashType.SHA512
):
    """
    Calculates a hash for provided data using specified algorithm.

    Parameters
    ----------
    data: Union[bytes, BinaryIO, Path]
        data to caclulate a hash for
    hash_type: config.HashType
        type of a hash algorithm to use, default is sha512

    Returns
    -------
    hashlib object:
        return an hash object provided by a `hashlib` module,
        please consult https://docs.python.org/3/library/hashlib.html
        for the details
    """

    if hash_type.value not in hashlib.algorithms_available:
        raise ValueError(
            f"Hash type '{hash_type.value}' is not"
            "supported by Python's `hashlib` module."
        )

    hash_method = getattr(hashlib, hash_type.value)()

    def _calc_io(fh):
        while True:
            _data = fh.read(4096)
            if not _data:
                break
            hash_method.update(_data)

    if isinstance(data, bytes):
        hash_method.update(data)
    elif isinstance(data, Path):
        with open(data, 'rb') as fh:
            _calc_io(fh)
    else:   # BinaryIO TODO consider strict type check for that
        _calc_io(data)

    return hash_method


def make_salt_logs_quiet():
    # TODO IMPROVE EOS-8473 better configuration way
    salt_logger = logging.getLogger('salt.fileclient')
    if salt_logger:
        salt_logger.setLevel(logging.WARNING)
