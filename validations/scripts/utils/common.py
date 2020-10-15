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
import os, sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
print (parent_dir_name)
sys.path.append(parent_dir_name + "/utils")

from pathlib import Path, PosixPath
from typing import (
    Tuple,
    Union,
    Optional,
    List
)

import config
from errors import (
   ProvisionerError, SubprocessCmdError
)

logger = logging.getLogger(__name__)

# Re-used utils.py contents. 
# Unnecessary checks can be removed later.

def validator_path_exists(instance, attribute, value):
    if value is None:
        if attribute.default is not None:
            raise ValueError(f"{attribute.name} should be defined")
    elif not value.exists():
        raise ValueError(f"Path {value} doesn't exist")


def converter_path_resolved(value):
    return value if value is None else Path(str(value)).resolve()


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
    def posix_path_representer(dumper_obj, posix_path_obj):
        return dumper_obj.represent_scalar(
            "tag:yaml.org,2002:str",
            str(posix_path_obj)
        )
    yaml.add_representer(PosixPath, posix_path_representer)

    return yaml.dump(
        data,
        default_flow_style=default_flow_style,
        canonical=canonical,
        width=width,
        indent=indent,
        **kwargs
    )

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
        logger.debug(f"Subprocess command {cmd}, kwargs: {_kwargs}")
        res = subprocess.run(cmd, **_kwargs)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.exception(f"Failed to run cmd '{cmd}'")
        raise SubprocessCmdError(cmd, _kwargs, repr(exc)) from exc
    else:
        logger.debug(f"Subprocess command resulted in: {res}")
        return res.returncode, res.stdout, res.stderr


def get_repo_archive_exclusions():
    exclude = []
    for d in config.REPO_BUILD_DIRS + ['*.swp']:
        exclude.extend(['--exclude', str(d)])
    return exclude


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
