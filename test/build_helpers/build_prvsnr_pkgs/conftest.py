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

from provisioner.vendor import attr
from provisioner import utils, inputs

from test import helper as h


@attr.s(auto_attribs=True)
class BundleOpts(inputs.ParserMixin):
    parser_prefix = 'build-'

    version: str = attr.ib(
        default='2.0.0',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "release version (source version)."
                    " Note. ignored for api package,"
                    " to set version for package please edit"
                    " 'api/python/provisioner/__metadata__.py'"
                )
            }
        }
    )
    pkg_version: str = attr.ib(
        default=1,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': (
                    "package version (release tag),"
                    " should be greater or equal 1"
                ),
                'metavar': 'INT'
            },
        },
        converter=int,
        validator=attr.validators.instance_of(int)
    )
    output: Union[str, Path] = attr.ib(
        default='.',
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "path to directory to output",
                'metavar': 'DIR'
            }
        },
        converter=utils.converter_path_resolved,
        validator=utils.validator_path_exists
    )

    def __attrs_post_init__(self):
        if not self.output.is_dir():
            raise ValueError(
                f"{self.output} is not a directory"
            )

        if self.pkg_version < 1:
            raise ValueError(
                "'pkg_version' should be greate or equal 1"
            )


def pytest_addoption(parser):
    h.add_options(
        parser, BundleOpts.prepare_args()
    )


@pytest.fixture(scope='session')
def bundle_opts_t():
    return BundleOpts
