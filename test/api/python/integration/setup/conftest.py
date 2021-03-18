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

import pytest
from pathlib import Path
from collections import defaultdict
from copy import deepcopy
from typing import Optional, Union

import test.helper as h

from provisioner.vendor import attr
from provisioner import inputs, utils


@attr.s(auto_attribs=True)
class SetupOpts(inputs.ParserMixin):
    parser_prefix = 'setup-'

    logdir: Optional[Union[str, Path]] = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "logdir to mount inside the container",
                'metavar': 'PATH'
            }
        },
        converter=utils.converter_path_resolved,
        validator=attr.validators.optional(
            utils.validator_dir_exists
        )
    )


def pytest_addoption(parser):
    h.add_options(
        parser, SetupOpts.prepare_args()
    )


@pytest.fixture(scope='session')
def custom_opts_t():
    return SetupOpts


@pytest.fixture(scope='module')
def env_level():
    return 'setup'


@pytest.fixture
def env_provider():
    return 'docker'


@pytest.fixture
def logdir_host(tmpdir_function, custom_opts):
    return (
        None if custom_opts.logdir is None else
        tmpdir_function / custom_opts.logdir.name
    )


@pytest.fixture
def hosts_spec(hosts_spec, hosts, tmpdir_function, custom_opts, logdir_host):
    res = deepcopy(hosts_spec)
    for host in hosts:
        host_glusterfs = tmpdir_function / host / 'srv/glusterfs'
        host_glusterfs.mkdir(parents=True)

        docker_settings = res[host]['remote']['specific']
        docker_settings['docker'] = defaultdict(
            dict, docker_settings.get('docker', {})
        )
        docker_settings = docker_settings['docker']
        docker_settings['privileged'] = True

        docker_settings['volumes'][str(host_glusterfs)] = {
            'bind': '/srv/glusterfs', 'mode': 'rw'
        }
        docker_settings['volumes']['/dev'] = {
            'bind': '/dev', 'mode': 'ro'
        }
        if custom_opts.logdir:
            docker_settings['volumes'][
                str(custom_opts.logdir)
            ] = {'bind': str(logdir_host), 'mode': 'rw'}
    return res
