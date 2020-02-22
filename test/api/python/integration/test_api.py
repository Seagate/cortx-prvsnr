import pytest
import logging
from pathlib import Path

from .helper import install_provisioner_api
from provisioner.config import PRVSNR_ROOT_DIR

logger = logging.getLogger(__name__)


@pytest.fixture(params=["py", "cli", "pycli"])
def api_type(request):
    return request.param


@pytest.fixture
def test_path():
    return 'test/api/python/integration/test_api_inner.py'


@pytest.fixture
def run_test(request, api_type, run_test, eos_hosts):
    def f(*args, env=None, **kwargs):
        if env is None:
            env = {}
        env['TEST_API_TYPE'] = api_type
        env['TEST_MINION_ID'] = eos_hosts['eosnode1']['minion_id']
        return run_test(*args, env=env, **kwargs)

    return f


# TODO split to different tests per each test case
@pytest.mark.timeout(1200)
@pytest.mark.isolated
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
        expected_exc='AuthenticationError'
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
        expected_exc='AuthorizationError'
    )
    run_test(
        mhosteosnode1, curr_user=username, username=username,
        password=password,
        expected_exc='AuthorizationError'
    )

    # CASE 3. add to group now
    mhosteosnode1.check_output(
        "groupadd {0} && usermod -a -G {0} {1}"
        .format(group, username)
    )
    run_test(mhosteosnode1, username=username, password=password)
    run_test(mhosteosnode1, curr_user=username, username=username, password=password)


# TODO
#   - timeout is high because of vbox env build,
#     need to dseparate build logic fromAexplore ways how
#     to separate that (less timeout if env is ready)
# Note. ntpd service doesn't work in docker without additional tricks
# (if it's actually possible)
@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_ntp_configuration(
    mhosteosnode1, run_test
):
    mhosteosnode1.check_output("yum install -y ntp")
    run_test(mhosteosnode1)
    # TODO
    #   - run ntp.config state and check that nothing changed


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_network_configuration(
    mhosteosnode1, run_test, eos_hosts, project_path
):
    mhosteosnode1.copy_to_host(
        project_path / "pillar/components/samples/ees.cluster.sls",
        host_path=Path(
            "{}/pillar/components/cluster.sls"
            .format(PRVSNR_ROOT_DIR)
        )
    )

    mhosteosnode1.check_output(
        "salt '{}' saltutil.refresh_pillar"
        .format(eos_hosts['eosnode1']['minion_id'])
    )

    run_test(mhosteosnode1)


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_eosupdate_repo_configuration(
    mhosteosnode1, run_test
):
    repo_dir = '/tmp/repo'
    iso_path = '/tmp/repo.iso'

    mhosteosnode1.check_output(
        "mkdir -p {repo_dir}"
        " && cp {rpm_path} {repo_dir}"
        " && yum install -y createrepo genisoimage"
        " && createrepo {repo_dir}"
        " && mkisofs -graft-points -r -l -iso-level 2 -J -o {iso_path} {repo_dir}"  # noqa: E501
        .format(
            repo_dir=repo_dir,
            rpm_path=mhosteosnode1.rpm_prvsnr,
            iso_path=iso_path
        )
    )
    run_test(mhosteosnode1, env={
        'TEST_REPO_DIR': repo_dir,
        'TEST_REPO_ISO_PATH': iso_path
    })


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_eos_update(
    mhosteosnode1, run_test
):
    run_test(mhosteosnode1)


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_pyinstaller_approach(
    mhosteosnode1, tmpdir_function, request
):
    # Note. python system libarary dir
    # python3 -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'

    import inspect

    app_script = (
        """
            import importlib

            import provisioner
            import provisioner.freeze

            pillar = provisioner.pillar_get()
            print(pillar)

            try:
                importlib.import_module('salt')
            except ImportError:
                pass
            else:
                assert False, "salt is available"

            try:
                importlib.import_module('provisioner._api')
            except ImportError:
                pass
            else:
                assert False, "provisioner._api is available"
        """.format(api_path=(mhosteosnode1.repo / 'api/python'))
    )
    app_script = inspect.cleandoc(app_script)

    app_path_local = tmpdir_function / 'myapp.py'
    app_path_local.write_text(app_script)
    app_path_remote = mhosteosnode1.copy_to_host(app_path_local)

    install_provisioner_api(mhosteosnode1)
    mhosteosnode1.check_output("pip3 install pyinstaller")

    mhosteosnode1.check_output(
        "cd {} && pyinstaller {}"
        .format(app_path_remote.parent, app_path_remote.name)
    )

    mhosteosnode1.check_output(
        "{0}/dist/{1}/{1}"
        .format(app_path_remote.parent, app_path_remote.stem)
    )
