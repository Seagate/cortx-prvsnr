import pytest
from pathlib import Path

from .helper import install_provisioner_api

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
    return 'eosnode-1'


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
