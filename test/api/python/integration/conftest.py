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

from test.helper import install_provisioner_api

collect_ignore = [
    'test_api_inner.py',
    'test_pillar_targets_inner.py',
    'test_rollback_inner.py',
    'test_hare_inner.py'
]


@pytest.fixture(scope='module')
def env_level():
    return 'singlenode-prvsnr-installed'


@pytest.fixture
def env_provider():
    return 'vbox'


@pytest.fixture
def test_path(request):
    return str(request.fspath)


@pytest.fixture
def test_host_hostname():
    return 'srvnode-1'


@pytest.fixture
def prepare_test_env(hosts_meta, project_path, test_path):

    def _f(test_mhost):
        _test_path = Path(str(test_path)).relative_to(project_path)
        inner_test_src = (
            _test_path.parent / "{}_inner.py".format(_test_path.stem)
        )

        # TODO limit to only necessary ones
        for mhost in hosts_meta.values():
            if mhost is test_mhost:
                install_provisioner_api(mhost)
                # TODO use requirements or setup.py
                mhost.check_output("pip3 install pytest==5.1.1")
                inner_tests_path = mhost.tmpdir / 'test.py'
                mhost.check_output("cp -f {} {}".format(
                    mhost.repo / inner_test_src,
                    inner_tests_path
                ))
                return inner_tests_path

        raise RuntimeError('no hosts matched')

    return _f


@pytest.fixture
def run_test(request, prepare_test_env):
    def f(
        mhost, curr_user=None, username=None, password=None,
        expected_exc=None, env=None
    ):
        inner_tests_path = prepare_test_env(mhost)

        script = (
            # "pytest -l -q -s --log-cli-level 0 -vv {}::{}"
            "pytest -l -q -s --log-cli-level warning --no-print-logs {}::{}"
            .format(
                inner_tests_path,
                request.node.originalname or request.node.name
            )
        )

        if expected_exc:
            script = "TEST_ERROR={} {}".format(expected_exc, script)

        if env:
            script = "{} {}".format(
                ' '.join(["{}={}".format(k, v) for k, v in env.items()]),
                script
            )

        if username:
            script = (
                "TEST_USERNAME={} TEST_PASSWORD={} {}"
                .format(username, password, script)
            )

            if curr_user:
                script = (
                    "su -l {} -c '{}'"
                    .format(curr_user, script)
                )

        return mhost.check_output(script)

    return f


import test.helper as h

@pytest.fixture(scope='session', params=h.LevelT)
def test_level(request):
    return request.param


@pytest.fixture(scope='session', params=h.TopicT)
def test_topic(request):
    return request.param


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if 'test_level' in item.fixturenames:
            item.add_marker(
                getattr(pytest.mark, item.callspec.params['test_level'].value)
            )
        if 'test_topic' in item.fixturenames:
            item.add_marker(
                getattr(pytest.mark, item.callspec.params['test_topic'].value)
            )
