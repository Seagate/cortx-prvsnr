import sys
import docker
import time
import json
from pathlib import Path
from collections import defaultdict

import pytest
import testinfra

import logging

from  .helper import (
    _docker_image_build, _docker_container_run, fixture_builder,
    safe_docker_container_name, safe_filename,
    PRVSNR_REPO_INSTALL_DIR, mock_system_cmd, restore_system_cmd
)

logger = logging.getLogger(__name__)

DOCKER_IMAGES_REPO = "seagate/ees-prvsnr"
MODULE_DIR = Path(__file__).parent.resolve()
SSH_KEY_FILE_NAME = "id_rsa.test"

ENV_LEVELS_HIERARCHY = {
    'base': None,
    'utils': 'base',
    'salt-installed': 'utils',
    'prvsnr-ready': 'base'
}

DEFAULT_EOS_SPEC = {
    'host_eosnode1': {
        'minion_id': 'eosnode-1',
        'is_primary': True,
    }, 'host_eosnode2': {
        'minion_id': 'eosnode-2',
        'is_primary': False,
    }
}


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "env_name(string): mark test to be run "
                   "in the specific environment"
    )
    config.addinivalue_line(
        "markers", "eos_spec(dict): mark test as expecting "
                   "specific EOS stack configuration, default: {}"
                   .format(json.dumps(DEFAULT_EOS_SPEC))
    )
    config.addinivalue_line(
        "markers", "hosts(list): mark test as expecting "
                   "the specified list of hosts, default: ['host']"
    )
    config.addinivalue_line(
        "markers", "isolated: mark test to be run in the isolated "
                   "environment instead of module wide shared"
    )
    config.addinivalue_line(
        "markers", "inject_repo: mark test as expecting repo injection "
                   "only for specified hosts, default: all hosts"
    )
    config.addinivalue_line(
        "markers", "inject_ssh_config: mark test as expecting ssh configuration "
                   "only for specified hosts, default: all hosts"
    )
    config.addinivalue_line(
        "markers", "mock_cmds(list): mark test as requiring "
                   "mocked system commands"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--envprovider", action='store', choices=['host', 'docker', 'vagrant'],
        default='docker',
        help="test environment provider, defaults to docker"
    )


@pytest.fixture(scope="session")
def project_path():
    return MODULE_DIR.parent


@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()


@pytest.fixture(scope="session")
def localhost():
    return testinfra.get_host('local://')


@pytest.fixture(scope='module')
def env_name():
    return 'centos7-base'


# function level is necessary to support env per test function
@fixture_builder(['module', 'function'], module_name=__name__)
def docker_image(request, docker_client, env_name, project_path):
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_name')
        if marker:
            env_name = marker.args[0]

    def _build(os_name, env_level):
        parent_env = ENV_LEVELS_HIERARCHY.get(env_level)
        if parent_env:
            _build(os_name, parent_env)
        ctx = str(project_path)

        _env_name = '-'.join([os_name, env_level])
        df_name = "Dockerfile.{}".format(_env_name)
        dockerfile = str(project_path / 'images' / 'docker' / df_name)
        image_name = "{}:{}".format(DOCKER_IMAGES_REPO, _env_name)
        return _docker_image_build(docker_client, dockerfile, ctx, image_name)

    _parts = env_name.split('-')
    return _build(_parts[0], '-'.join(_parts[1:]))


@pytest.fixture(scope='module')
def post_docker_run():
    def f(container):
        pass
    return f


@pytest.fixture(scope='module')
def post_host_run_hook():
    def f(host, hostname, ssh_config, request):
        pass
    return f


def docker_container(request, docker_client, post_docker_run):
    try:
        suffix = request.fixturename.split('docker_container')[1]
    except IndexError:
        suffix = None

    container_name = "{}{}".format(safe_docker_container_name(request.node.nodeid), suffix)

    image = request.getfixturevalue("docker_image_{}".format(request.scope))
    try:
        container = _docker_container_run(docker_client, image, container_name)
        post_docker_run(container)
        yield container
    finally:
        try:
            # 'container' might be not assigned yet here
            _container = docker_client.containers.get(container_name)
        except:
            # container with the name might not be even created yet
            pass
        else:
            _container.remove(force=True)


@pytest.fixture
def tmpdir(request, tmp_path_factory):
    return tmp_path_factory.mktemp(safe_filename(request.node.nodeid))


@pytest.fixture
def ssh_key(tmpdir):
    key = tmpdir / SSH_KEY_FILE_NAME
    with open(str(MODULE_DIR / SSH_KEY_FILE_NAME)) as f:
        key.write_text(f.read())
    key.chmod(0o600)
    return key


@pytest.fixture
def ssh_config(request, tmpdir):
    return tmpdir / "ssh_config"


@pytest.fixture
def hosts(request):
    hosts = ['host']

    marker = request.node.get_closest_marker('hosts')
    if marker:
        hosts = marker.args[0]

    return {
        host: request.getfixturevalue(host) for host in hosts
    }


@pytest.fixture
def mock_hosts(hosts, request):
    cmds = []

    marker = request.node.get_closest_marker('mock_cmds')
    if marker:
        cmds = marker.args[0]

    for host in hosts.values():
        assert host is not localhost  # TODO more clever check
        for cmd in cmds:
            mock_system_cmd(host, cmd)

    yield

    for host in hosts.values():
        for cmd in cmds:
            restore_system_cmd(host, cmd)


@pytest.fixture
def install_repo(hosts, localhost, project_path, ssh_config):
    for host in hosts.values():
        host.check_output(
            "mkdir -p {}"
            .format(PRVSNR_REPO_INSTALL_DIR)
        )
        hostname = host.check_output('hostname')

        for path in ('files', 'pillar', 'srv', 'cli'):
            localhost.check_output(
                "scp -r -F {} {} {}:{}".format(
                    ssh_config,
                    project_path / path,
                    hostname,
                    PRVSNR_REPO_INSTALL_DIR
                )
            )


@pytest.fixture
def inject_repo(hosts, localhost, project_path, ssh_config, request):
    repo_paths = {}
    host_repo_base_dir = '/tmp'
    target_hosts = list(hosts)

    marker = request.node.get_closest_marker('inject_repo')
    if marker:
        target_hosts = marker.args[0]

    for label, host in hosts.items():
        if label in target_hosts:
            hostname = host.check_output('hostname')
            localhost.check_output(
                "scp -r -F {} {} {}:{}".format(
                    ssh_config, project_path, hostname, host_repo_base_dir
                )
            )
            repo_paths[label] = Path(host_repo_base_dir) / project_path.name
    return repo_paths


@pytest.fixture
def inject_ssh_config(hosts, localhost, ssh_config, ssh_key, request):
    target_hosts = list(hosts)

    marker = request.node.get_closest_marker('inject_ssh_config')
    if marker:
        target_hosts = marker.args[0]

    for label, host in hosts.items():
        if label in target_hosts:
            hostname = host.check_output('hostname')
            for path in (ssh_config, ssh_key):
                host.check_output("mkdir -p {}".format(path.parent))
                localhost.check_output(
                    "scp -p -F {} {} {}:{}".format(
                        ssh_config, path, hostname, path
                    )
                )
            host.check_output("mkdir -p ~/.ssh".format(path.parent))
            host.check_output('cp -p {} ~/.ssh/config'.format(ssh_config))


@pytest.fixture
def eos_spec(request):
    marker = request.node.get_closest_marker('eos_spec')
    spec = marker.args[0] if marker else DEFAULT_EOS_SPEC
    return spec


# eos_spec sanity checks
@pytest.fixture
def _eos_spec(eos_spec):
    assert len({k: v for k, v in eos_spec.items() if v['is_primary']}) == 1
    return eos_spec


@pytest.fixture
def eos_hosts(hosts, _eos_spec, request):
    _hosts = defaultdict(dict)
    for label, host in hosts.items():
        if label in _eos_spec:
            _hosts[label]['host'] = host
            _hosts[label]['minion_id'] = _eos_spec[label]['minion_id']
            _hosts[label]['is_primary'] = _eos_spec[label].get('is_primary', True)

    return _hosts


@pytest.fixture
def eos_primary_host(eos_hosts):
    return [v for v in eos_hosts.values() if v['is_primary']][0]['host']


@pytest.fixture
def eos_primary_host_ip(eos_primary_host):
    return eos_primary_host.interface("eth0").addresses[0]


@pytest.fixture
def configure_salt(eos_hosts, install_repo, eos_primary_host_ip):
    cli_dir = PRVSNR_REPO_INSTALL_DIR / 'cli' / 'src'

    for label, host_spec in eos_hosts.items():
        minion_id = host_spec['minion_id']
        is_primary = (
            'true' if host_spec['is_primary'] else 'false'
        )
        primary_host = (
            "localhost" if host_spec['is_primary'] else eos_primary_host_ip
        )
        host_spec['host'].check_output(
            ". {} && configure_salt '{}' '' '' '' {} {}".format(
                cli_dir / 'functions.sh', minion_id, is_primary, primary_host
            )
        )


@pytest.fixture
def accept_salt_keys(eos_hosts, install_repo, eos_primary_host):
    cli_dir = PRVSNR_REPO_INSTALL_DIR / 'cli' / 'src'

    for label, host_spec in eos_hosts.items():
        eos_primary_host.check_output(". {} && accept_salt_keys '{}'".format(
            cli_dir / 'functions.sh', host_spec['minion_id'])
        )

    eos_primary_host.check_output("salt '*' mine.update")


def build_host_fixture(suffix=None, module_name=__name__):
    # TODO not the best way since it should correlate with outside naming policy
    host_fixture_name = '_'.join([part for part in ['host', suffix] if part])

    # TODO would be handy to have that as an attribute of the host
    # TODO there might be some cheaper way (e.g. get from testinfra host object)
    def hostname(request):
        host = request.getfixturevalue(host_fixture_name)
        return host.check_output('hostname')

    # TODO would be handy to have that as an attribute of the host
    def host_tmp_path(request, tmp_path):
        host = request.getfixturevalue(host_fixture_name)
        host.check_output("mkdir -p {}".format(tmp_path))
        return tmp_path

    docker_container_fixtures = {
        scope: fixture_builder(
            scope,
            suffix=suffix,
            module_name=module_name
        )(docker_container) for scope in ('module', 'function')
    }

    fixture_builder(
        'function',
        suffix=suffix,
        module_name=module_name,
        name_with_scope=False
    )(hostname)

    fixture_builder(
        'function',
        suffix=suffix,
        module_name=module_name,
        name_with_scope=False
    )(host_tmp_path)

    @fixture_builder(
        "function", suffix=suffix, module_name=module_name,
        name_with_scope=False
    )
    def host(localhost, request):
        envprovider = request.config.getoption("envprovider")
        if envprovider == 'host':
            return localhost
        elif envprovider == 'docker':
            ssh_key = request.getfixturevalue('ssh_key')
            ssh_config = request.getfixturevalue('ssh_config')
            post_host_run_hook = request.getfixturevalue('post_host_run_hook')

            scope = (
                'function' if request.node.get_closest_marker('isolated')
                else 'module'
            )
            container = request.getfixturevalue(
                docker_container_fixtures[scope].__name__
            )

            # update container data
            container.reload()

            _host = testinfra.get_host(container.id, connection='docker')
            # TODO there might be some cheaper way (e.g. get from testinfra host object)
            _hostname = _host.check_output('hostname')

            # prepare ssh configuration
            ssh_config.touch(mode=0o600, exist_ok=True)
            with ssh_config.open('a') as f:
                f.write((
                    "Host {}\n"
                    "  Hostname {}\n"
                    "  Port 22\n"
                    "  User {}\n"
                    "  UserKnownHostsFile /dev/null\n"
                    "  StrictHostKeyChecking no\n"
                    "  IdentityFile {}\n"
                    "  IdentitiesOnly yes\n"
                    "  LogLevel FATAL\n"
                ).format(
                    _hostname,
                    _host.interface("eth0").addresses[0],
                    'root',
                    str(ssh_key))
                )

            hostspec = "ssh://{}".format(_hostname)

            # Wait ssh to be up
            service = _host.service

            # TODO service name is 'ssh' on debian, ubuntu, ... ???
            service_name = 'sshd'
            while not service(service_name).is_running:
                time.sleep(.5)

            _host = testinfra.get_host(hostspec, ssh_config=str(ssh_config))
            post_host_run_hook(_host, _hostname, ssh_config, request)

            return _host
        else:  # vagrant TODO
            pytest.skip()
            return

# default 'host' fixture is always present
build_host_fixture()
# also host fixtures for EOS stack makes sense
build_host_fixture('eosnode1')
build_host_fixture('eosnode2')
