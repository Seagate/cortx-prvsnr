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

from test import helper as h


prvsnr_pytest_options = {
    "docker-mount-dev": dict(
        action='store_true',
        help="Mount /dev into docker containers, default: False"
    ),
    "no-docker-mount-glusterfs": dict(
        action='store_false',
        help=(
            "Mount /dev into docker containers, "
            "default: False (means do mount)"
        )
    ),
    "root-passwd": dict(
        action='store',
        help="Mount /dev into docker containers",
        default='root'
    ),
    # TODO validation
    "nodes-num": dict(
        action='store', type=int,
        help="Number of nodes",
        default=1
    )
}


def pytest_addoption(parser):
    h.add_options(parser, prvsnr_pytest_options)


@pytest.fixture(scope="session")
def options_list(options_list):
    return options_list + list(prvsnr_pytest_options)


@pytest.fixture(scope='session')
def nodes_num(request):
    return request.config.getoption("nodes_num")


@pytest.fixture(scope='session')
def root_passwd(request):
    return request.config.getoption("root_passwd")


@pytest.fixture(scope='session')
def ask_proceed():

    def _f():
        input('Press any key to continue...')

    return _f
