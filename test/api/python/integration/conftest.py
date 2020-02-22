import pytest

from .helper import install_provisioner_api

collect_ignore = ["test_api_inner.py", "test_pillar_targets_inner.py"]


@pytest.fixture(scope='module')
def env_level():
    return 'singlenode-prvsnr-installed'


@pytest.fixture
def env_provider():
    return 'vbox'


@pytest.fixture
def test_path():
    raise NotImplementedError("define 'test_path' fixture")


@pytest.fixture
def prepare_test_env(hosts_meta, test_path):
    # TODO limit to only necessary ones
    for mhost in hosts_meta.values():
        install_provisioner_api(mhost)
        mhost.check_output("pip3 install pytest==5.1.1")  # TODO use requirements or setup.py
        inner_tests_path = mhost.tmpdir / 'test.py'
        mhost.check_output("cp -f {} {}".format(
            mhost.repo / test_path, inner_tests_path)
        )
        return inner_tests_path


@pytest.fixture
def run_test(request):
    def f(mhost, curr_user=None, username=None, password=None, expected_exc=None, env=None):
        inner_tests_path = request.getfixturevalue('prepare_test_env')

        script = (
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
