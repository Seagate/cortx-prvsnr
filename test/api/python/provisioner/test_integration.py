import pytest
import logging

logger = logging.getLogger(__name__)

@pytest.fixture
def vagrant_default_ssh():
    return True

@pytest.fixture
def prepare_test_env(request, hosts_meta):
    # TODO limit to only necessary ones
    for mhost in hosts_meta.values():
        mhost.check_output("pip3 install {}".format(mhost.repo / 'api/python'))
        mhost.check_output("pip3 install pytest==5.1.1")  # TODO use requirements or setup.py
        inner_tests_path = mhost.tmpdir / 'test.py'
        mhost.check_output("cp -f {} {}".format(
            mhost.repo / 'test/api/python/provisioner/test_integration_inner.py', inner_tests_path)
        )
        return inner_tests_path


@pytest.fixture
def run_test(request):
    def f(mhost, curr_user=None, username=None, password=None, expected_exc=None):
        inner_tests_path = request.getfixturevalue('prepare_test_env')

        script = (
            "pytest -l -q -s --log-cli-level warning --no-print-logs {}::{}"
            .format(inner_tests_path, request.node.name)
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

        if expected_exc:
            script = "TEST_ERROR={} {}".format(expected_exc, script)

        if expected_exc:
            res = mhost.run(script)
            assert res.rc != 0
            return res
        else:
            return mhost.check_output(script)

    return f

# TODO
#   - timeout is high because of vbox env build,
#     need to dseparate build logic fromAexplore ways how
#     to separate that (less timeout if env is ready)
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.env_level('singlenode-prvsnr-installed')
@pytest.mark.env_provider('vbox')
@pytest.mark.hosts(['eosnode1'])
def test_ntp_configuration(
    mhosteosnode1, run_test
):
    mhosteosnode1.check_output("yum install -y ntp")
    run_test(mhosteosnode1)
    # TODO
    #   - run ntp.config state and check that nothing changed


@pytest.mark.timeout(1200)
@pytest.mark.skip(reason="EOS-1740")
@pytest.mark.isolated
@pytest.mark.env_level('singlenode-prvsnr-installed')
@pytest.mark.env_provider('vbox')
@pytest.mark.hosts(['eosnode1'])
def test_network_configuration(
    mhosteosnode1, run_test
):
    run_test(mhosteosnode1)


# TODO split to different tests per each test case
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.env_level('singlenode-prvsnr-installed')
@pytest.mark.env_provider('vbox')
@pytest.mark.hosts(['eosnode1'])
def test_external_auth(
    mhosteosnode1, run_test
):
    username = 'someuser'
    password = '123456'
    group = 'prvsnrusers'  # check for user from default group `prvsnrusers`

    # CASE 1. do not create user at first
    run_test(
        mhosteosnode1, username=username, password=password,
        expected_exc='salt.exceptions.AuthenticationError'
    )

    # CASE 2. create user but do not add to group for now
    mhosteosnode1.check_output(
        "adduser {0} && echo {1} | passwd --stdin {0}"
        .format(username, password)
    )

    # Note. changing current user actually might be not needed
    # but it's better to cover that case as well
    run_test(
        mhosteosnode1, username=username, password=password,
        expected_exc='salt.exceptions.AuthorizationError'
    )
    run_test(
        mhosteosnode1, curr_user=username, username=username,
        password=password,
        expected_exc='salt.exceptions.AuthorizationError'
    )

    # CASE 3. add to group now
    mhosteosnode1.check_output(
        "groupadd {0} && usermod -a -G {0} {1}"
        .format(group, username)
    )
    run_test(mhosteosnode1, username=username, password=password)
    run_test(mhosteosnode1, curr_user=username, username=username, password=password)
