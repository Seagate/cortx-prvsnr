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

import configparser
import logging
import subprocess
import time
import yaml
from shlex import quote

from pathlib import Path, PosixPath
from typing import (
    Tuple,
    Union,
    Optional,
    List
)

from . import config

from .errors import (
    BadPillarDataError, ProvisionerError, SubprocessCmdError
)

logger = logging.getLogger(__name__)


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


def converter_path(value):
    return value if value is None else Path(str(value))


def file_scheme_key_converter(value: dict):
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


def validator__subclass_of(classinfo):
    def _f(attribute, value):
        if not issubclass(value, classinfo):
            raise TypeError(
                f"'{attribute.name}' must be subclass of {classinfo}"
            )


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
                raise ProvisionerError(f'no more tries for {name}')


def run_subprocess_cmd(cmd, **kwargs):
    _kwargs = dict(
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    _kwargs.update(kwargs)
    _kwargs['check'] = True

    if type(cmd) is str:
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
            f"Subprocess command {res.args} resulted in - stdout: {res.stdout}, "
            f"returncode: {res.returncode},stderr: {res.stderr}"
        )
        return res


def get_repo_archive_exclusions():
    exclude = []
    for d in config.REPO_BUILD_DIRS + ['*.swp']:
        exclude.extend(['--exclude', str(d)])
    return exclude


def repo_tgz(
    dest: Path,
    project_path: Optional[Path] = None,
    version: str = None,
    include_dirs: Optional[List] = None
):
    if project_path is None:
        project_path = config.PROJECT_PATH

    if not project_path:
        raise ValueError('project path is not specified')

    if include_dirs is None:
        include_dirs = ['.']

    include_dirs = [str(d) for d in include_dirs]

    # treat the version as git commit/branch/tag ...
    if version:
        cmd = (
            ['git', 'archive', '--format=tar.gz', version, '-o', str(dest)] +
            include_dirs
        )
    # do raw archive with uncommitted/untracked changes otherwise
    else:
        exclude = get_repo_archive_exclusions()

        cmd = (
            ['tar', '-czf',  str(dest)] +
            exclude +
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
            "srvnode" in section
            and (
                node_dict[section] != parser_obj[section]["hostname"]
            )
        ):
            msg = (
                "Hostname values from config.ini and CLI did not match. "
                f"{node_dict[section]} != {parser_obj[section]['hostname']}"
            )
            raise ValueError(msg)
