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
from provisioner import utils

from test import helper as h


@attr.s(auto_attribs=True)
class BundleOpts:
    type: str
    version: str
    output: Union[str, Path] = attr.ib(
        converter=utils.converter_path_resolved,
        validator=utils.validator_path
    )
    orig_single_iso: Union[str, Path] = attr.ib(
        converter=utils.converter_path_resolved,
        validator=utils.validator_path_exists
    )

    def __attrs_post_init__(self):
        if self.type == 'all' and not self.output.is_dir():
            raise ValueError(f"{self.output} is not a directory")


prvsnr_pytest_options = {
    "bundle-orig-single-iso": dict(
        action='store',
        help="original CORTX single ISO for partial use",
        default=None,
        metavar='PATH'
    ),
    "bundle-output": dict(
        action='store',
        help="path to file or directory to output",
        default=h.PROJECT_PATH,
        metavar='PATH'
    ),
    "bundle-type": dict(
        action='store',
        help="type of the bundle",
        default='deploy-bundle',
        metavar='TYPE',
        choices=(h.BUNDLE_TYPES + ['all'])
    ),
    "bundle-version": dict(
        action='store',
        help="version of the release, ignored if 'all' type is used",
        default='2.0.0',
        metavar='PATH'
    )
}


def pytest_addoption(parser):
    h.add_options(parser, prvsnr_pytest_options)


@pytest.fixture(scope="session")
def options_list(options_list):
    return options_list + list(prvsnr_pytest_options)


@pytest.fixture(scope='session')
def bundle_opts(request):
    opts = vars(request.config.option)
    return BundleOpts(
        **{
            k[7:]: opts[k] for k in list(opts)
            if k[7:] in attr.fields_dict(BundleOpts)
        }
    )


@pytest.fixture(scope='session')
def orig_single_iso_on_host(tmpdir_session, bundle_opts):
    if bundle_opts.orig_single_iso:
        return Path('/opt/iso') / bundle_opts.orig_single_iso.name


@pytest.fixture(scope='session')
def bundle_script_path_f():
    def _f(mhost):
        return mhost.repo / h.BUILD_BUNDLE_SCRIPT.relative_to(h.PROJECT_PATH)

    return _f


@pytest.fixture
def hosts_spec(
    hosts_spec, hosts, request, bundle_opts, orig_single_iso_on_host
):
    res = deepcopy(hosts_spec)
    for host in hosts:
        docker_settings = res[host]['remote']['specific']
        docker_settings['docker'] = defaultdict(
            dict, docker_settings.get('docker', {})
        )
        docker_settings = docker_settings['docker']

        if bundle_opts.orig_single_iso:
            docker_settings['privileged'] = True
            docker_settings['volumes']['/dev'] = {
                'bind': '/dev', 'mode': 'ro'
            }
            docker_settings['volumes'][
                str(bundle_opts.orig_single_iso.parent)
            ] = {'bind': str(orig_single_iso_on_host.parent), 'mode': 'ro'}

    return res
