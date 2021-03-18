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
from typing import Union
from pathlib import Path
from copy import deepcopy
from collections import defaultdict

from provisioner.vendor import attr
from provisioner import utils, inputs

from test import helper as h


@attr.s(auto_attribs=True)
class BundleOpts(inputs.ParserMixin):
    parser_prefix = 'build-'

    type: str = attr.ib(
        default='deploy-bundle',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "type of the bundle",
                'metavar': 'TYPE',
                'choices': ([t.value for t in h.BundleT] + ['all'])
            }
        }
    )
    version: str = attr.ib(
        default='2.0.0',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "version of the release, ignored if 'all' type is used"
            }
        }
    )
    output: Union[str, Path] = attr.ib(
        default='.',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "path to file or directory to output"
            }
        },
        converter=utils.converter_path_resolved,
        validator=utils.validator_path
    )
    orig_single_iso: Union[str, Path] = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "original CORTX single ISO for partial use",
                'metavar': 'PATH'
            }
        },
        converter=utils.converter_path_resolved,
        validator=utils.validator_path_exists
    )
    prvsnr_pkg: Union[str, Path] = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "PATH to provisioner core rpm package",
                'metavar': 'PATH'
            }
        },
        converter=utils.converter_path_resolved,
        validator=utils.validator_path_exists
    )
    prvsnr_api_pkg: Union[str, Path] = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "PATH to provisioner API rpm package",
                'metavar': 'PATH'
            }
        },
        converter=utils.converter_path_resolved,
        validator=utils.validator_path_exists
    )

    def __attrs_post_init__(self):
        if not self.output.is_dir():
            if self.type == 'all':
                raise ValueError(
                    f"{self.output} is not a directory"
                    " and can't be used to output all bundles"
                )

            if not self.output.parent.is_dir():
                raise ValueError(
                    f"{self.output.parent} is not a directory"
                )


def pytest_addoption(parser):
    h.add_options(
        parser, BundleOpts.prepare_args()
    )


@pytest.fixture(scope='session')
def custom_opts_t():
    return BundleOpts


@pytest.fixture(scope='session')
def orig_single_iso_on_host(tmpdir_session, custom_opts):
    if custom_opts.orig_single_iso:
        return Path('/opt/iso') / custom_opts.orig_single_iso.name


@pytest.fixture(scope='session')
def bundle_script_path_f():
    def _f(mhost):
        return mhost.repo / h.BUILD_BUNDLE_SCRIPT.relative_to(h.PROJECT_PATH)

    return _f


@pytest.fixture
def hosts_spec(
    hosts_spec, hosts, request, custom_opts, orig_single_iso_on_host
):
    res = deepcopy(hosts_spec)
    for host in hosts:
        docker_settings = res[host]['remote']['specific']
        docker_settings['docker'] = defaultdict(
            dict, docker_settings.get('docker', {})
        )
        docker_settings = docker_settings['docker']

        if custom_opts.orig_single_iso:
            docker_settings['privileged'] = True
            docker_settings['volumes']['/dev'] = {
                'bind': '/dev', 'mode': 'ro'
            }
            docker_settings['volumes'][
                str(custom_opts.orig_single_iso.parent)
            ] = {'bind': str(orig_single_iso_on_host.parent), 'mode': 'ro'}

    return res
