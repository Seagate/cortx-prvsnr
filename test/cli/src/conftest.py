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

import test.cli.src.helper as h


@pytest.fixture
def run_script(mlocalhost, tmpdir_function, request):
    def _f(
        *args,
        mhost=None,
        trace=False,
        stderr_to_stdout=True,
        script_name=None,
        env=None
    ):
        if script_name is None:
            script_name = request.getfixturevalue('script_name')

        if mhost is None:
            mhost = request.getfixturevalue('mhost')

        return h.run_script(
            mhost,
            mhost.repo / 'cli/src' / script_name,
            *args,
            trace=trace,
            stderr_to_stdout=stderr_to_stdout,
            env=env
        )
    return _f
