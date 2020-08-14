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

import pytest
import argparse

def pytest_addoption(parser):
    parser.addoption(
        "--bvt-repo-path", action='store',
        default='./eos-test.tgz',
        help="path to eos-test repo tar gzipped file"
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
def options_list(options_list):
    return (
        options_list +
        ["bvt-repo-path", "bvt-test-targets", "bvt-results-path"]
    )
