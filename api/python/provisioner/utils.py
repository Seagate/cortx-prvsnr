#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import yaml
import logging
import time
from typing import Tuple, Union
from pathlib import Path
from typing import Optional, List
import subprocess

from . import config

from .errors import (
    BadPillarDataError, ProvisionerError, SubprocessCmdError
)

logger = logging.getLogger(__name__)


# TODO test
def load_yaml_str(data):
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError as exc:
        logger.exception("Failed to load pillar data")
        raise BadPillarDataError(str(exc))


# TODO test
def dump_yaml_str(
    data,
    width=1,
    indent=4,
    default_flow_style=False,
    canonical=False,
    **kwargs
):
    return yaml.safe_dump(
        data,
        default_flow_style=default_flow_style,
        canonical=canonical,
        width=width,
        indent=indent,
        **kwargs
    )


# TODO test
# TODO streamed read
def load_yaml(path):
    path = Path(str(path))
    try:
        return load_yaml_str(path.read_text())
    except yaml.YAMLError as exc:
        logger.exception("Failed to load pillar data")
        raise BadPillarDataError(str(exc))


# TODO test
# TODO streamed write
def dump_yaml(path, data, **kwargs):
    path = Path(str(path))
    path.write_text(dump_yaml_str(data, **kwargs))


# TODO IMPROVE:
#   - exceptions in check callback
def ensure(
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
                raise ProvisionerError('no more tries')


# TODO TEST CORTX-8473
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
        # TODO IMPROVE CORTX-8473 logging level
        logger.debug(f"Subprocess command {cmd}, kwargs: {_kwargs}")
        res = subprocess.run(cmd, **_kwargs)
    except subprocess.CalledProcessError as exc:
        logger.exception(f"Failed to run cmd '{cmd}'")
        raise SubprocessCmdError(cmd, _kwargs, repr(exc)) from exc
    else:
        logger.debug(f"Subprocess command resulted in: {res}")
        return res


# TODO TEST CORTX-8473
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
        exclude = []
        for d in config.REPO_BUILD_DIRS + ['*.swp']:
            exclude.extend(['--exclude', str(d)])

        cmd = (
            ['tar', '-czf',  str(dest)] +
            exclude +
            ['-C', str(project_path)] +
            include_dirs
        )

    run_subprocess_cmd(cmd)

    return dest
