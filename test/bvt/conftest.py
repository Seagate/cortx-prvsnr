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


def pytest_addoption(parser):
    parser.addoption(
        "--bvt-repo-path", action='store',
        default='./cortx-test.tgz',
        help="path to cortx-test repo tar gzipped file"
    )
    parser.addoption(
        "--bvt-test-targets", action='store',
        default='avocado_test/bvt_test.py',
        help="bvt test targets to run"
    )
    parser.addoption(
        "--bvt-results-path", action='store',
        default='./bvt.job-results.tgz',
        help="path to tar gzipped archive with bvt test job result"
    )


@pytest.fixture(scope="session")
def run_options(run_options):
    return (
        run_options +
        ["bvt-repo-path", "bvt-test-targets", "bvt-results-path"]
    )
