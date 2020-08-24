#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
# please email opensource@seagate.com or cortx-questions@seagate.com."
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
