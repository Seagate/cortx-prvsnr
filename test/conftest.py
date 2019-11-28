import docker
import time
import json
from pathlib import Path
from collections import defaultdict

import pytest
import testinfra

import logging

import test.helper as h
from .helper import (
    _docker_image_build, _docker_container_run, fixture_builder,
    safe_docker_container_name, safe_vagrant_machine_name, safe_filename,
    safe_hostname,
    PRVSNR_REPO_INSTALL_DIR, mock_system_cmd, restore_system_cmd
)

logger = logging.getLogger(__name__)

DOCKER_IMAGES_REPO = "seagate/ees-prvsnr"
MODULE_DIR = Path(__file__).resolve().parent
SSH_KEY_FILE_NAME = "id_rsa.test"

OS_NAMES = [
    'centos7'
]

ENV_LEVELS_HIERARCHY = {
    'base': None,
    'utils': 'base',
    'rpmbuild': 'base',
    'network-manager-installed': 'base',
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
        "--envprovider", action='store', choices=['host', 'docker', 'vbox'],
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


@pytest.fixture(scope='session')
def ssh_key(tmpdir_session):
    key = tmpdir_session / SSH_KEY_FILE_NAME
    with open(str(MODULE_DIR / SSH_KEY_FILE_NAME)) as f:
        key.write_text(f.read())
    key.chmod(0o600)
    return key


@pytest.fixture(scope="session")
def vagrant_global_status_prune(localhost):
    localhost.check_output('vagrant global-status --prune')


# TODO multi platforms case
@pytest.fixture(scope="session")
def vbox_seed_machine(request, project_path, vagrant_global_status_prune, localhost):
    if request.config.getoption("envprovider") != 'vbox':
        return None

    platform = 'centos7'
    machine_suffix = "{}-base".format(platform)
    machine_name = "{}.{}".format(DOCKER_IMAGES_REPO.replace('/', '.'), machine_suffix)
    vagrantfile_name = "Vagrantfile.{}".format(machine_suffix)
    vagrantfile = project_path / 'images' / 'vagrant' / vagrantfile_name

    machine = h.VagrantMachine(
        machine_name, vagrantfile=vagrantfile
    )
    status = machine.status(update=True)
    # TODO move that specific to VagrantMachine API
    if status['state'][0] == 'not_created':
        # create VM
        machine.up()
        machine.cmd('halt')
        machine.cmd('snapshot', 'save', machine.name, 'initial --force')
    else:
        # TODO do that only if rebuild base vagrant box
        machine.cmd('snapshot', 'restore', machine.name, 'initial --no-start')


# TODO DOCS
@pytest.fixture(scope='session')
def rpm_prvsnr(request, project_path, localhost, tmpdir_session):
    envprovider = request.config.getoption("envprovider")

    # TODO DOCS : example how to run machine out of fixture scope
    with build_remote(
        envprovider, request, 'centos7', 'rpmbuild'
    ) as remote:
        meta = discover_remote(request, remote)
        repo_path = h.inject_repo(localhost, meta.host, meta.ssh_config, project_path)
        h.check_output(
            meta.host, 'cd {} && sh -x build/rpms/buildrpm.sh'.format(repo_path)
        )
        rpm_remote_path = h.check_output(
            meta.host, 'ls ~/rpmbuild/RPMS/x86_64/eos-prvsnr*.rpm'
        ).strip()
        rpm_remote_path = Path(rpm_remote_path)
        rpm_local_path = tmpdir_session / rpm_remote_path.name
        localhost.check_output(
            "scp -F {} {}:{} {}".format(
                meta.ssh_config,
                meta.hostname,
                rpm_remote_path,
                rpm_local_path
            )
        )
        return rpm_local_path


@pytest.fixture(scope='module')
def env_name():
    return 'centos7-base'


def env_fixture_suffix(os_name, env_level):
    return "{}_{}".format(os_name, env_level.replace('-', '_'))


def build_docker_image_fixture(os_name, env_level):

    def docker_image(request, docker_client, project_path):
        parent_env = ENV_LEVELS_HIERARCHY.get(env_level)
        if parent_env:
            _ = request.getfixturevalue(
                "docker_image_{}".format(
                    env_fixture_suffix(os_name, parent_env))
            )
        ctx = str(project_path)
        _env_name = '-'.join([os_name, env_level])
        df_name = "Dockerfile.{}".format(_env_name)
        dockerfile = str(project_path / 'images' / 'docker' / df_name)
        image_name = "{}:{}".format(DOCKER_IMAGES_REPO, _env_name)
        return _docker_image_build(docker_client, dockerfile, ctx, image_name)

    fixture_builder(
        'session',
        suffix=env_fixture_suffix(os_name, env_level),
        module_name=__name__,
        name_with_scope=False
    )(docker_image)


for os_name in OS_NAMES:
    for env_level in ENV_LEVELS_HIERARCHY:
        build_docker_image_fixture(os_name, env_level)


def build_vagrant_box_fixture(os_name, env_level):

    def vagrant_box(request, project_path):
        parent_env = ENV_LEVELS_HIERARCHY.get(env_level)
        if parent_env:
            _ = request.getfixturevalue(
                "vagrant_box_{}".format(
                    env_fixture_suffix(os_name, parent_env))
            )
        _env_name = '-'.join([os_name, env_level])
        pf_name = "packer.{}.json".format(_env_name)
        packerfile = project_path / 'images' / 'vagrant' / pf_name
        box_path = project_path / '.boxes' / _env_name / 'package.box'

        # TODO smarter logic of boxes rebuild, triggered when:
        #  - parent env is changed
        #  - provisioning scripts and other related sources are changed
        # box_updated = False
        if not box_path.exists():
            # TODO smarter logic of seed machine reference
            # build seed machine beforehand
            if parent_env is None:
                request.getfixturevalue('vbox_seed_machine')

            # TODO pytest options to turn on packer debug
            # TODO add box to vagrant here: it should prevent auto add by
            #      vagrant during 'vagrant up' where it uses path to source box
            packer = h.Packer(packerfile)
            packer.build('--force')
            # box_updated = True

        box = h.VagrantBox(
            "{}.{}".format(DOCKER_IMAGES_REPO.replace('/', '.'), _env_name),
            box_path
        )

        # TODO add only if not exists or updated
        h.Vagrant().box(
            "add --provider virtualbox --name",
            box.name,
            '--force',
            str(box.path)
        )

        return box

    fixture_builder(
        'session',
        suffix=env_fixture_suffix(os_name, env_level),
        module_name=__name__,
        name_with_scope=False
    )(vagrant_box)


for os_name in OS_NAMES:
    for env_level in ENV_LEVELS_HIERARCHY:
        build_vagrant_box_fixture(os_name, env_level)

'''
def build_vagrant_machine_shared_fixture(os_name, env_level):

    def vagrant_machine_shared(request, project_path, tmp_path_factory):
        box = request.getfixturevalue(
            "vagrant_box_{}".format(
                env_fixture_suffix(os_name, env_level))
        )
        machine_name = safe_vagrant_machine_name("{}-shared".format(box.name))
        tmpdir = tmp_path_factory.mktemp(safe_filename(machine_name))
        vagrantfile_dest = str(tmpdir / 'Vagrantfile')
        machine = VagrantMachine(
            machine_name, box=box, vagrantfile_dest=vagrantfile_dest
        )
        try:
            machine.destroy()
            machine.up()
            machine.cmd('halt')
            # TODO hardcoded
            machine.cmd('snapshot', 'save', machine.name, 'initial --force')
            machine.cmd('halt --force')
            yield machine
        finally:
            machine.destroy()

    fixture_builder(
        'session',
        suffix=env_fixture_suffix(os_name, env_level),
        module_name=__name__,
        name_with_scope=False
    )(vagrant_machine_shared)


for os_name in OS_NAMES:
    for env_level in ENV_LEVELS_HIERARCHY:
        build_vagrant_machine_shared_fixture(os_name, env_level)


@fixture_builder(['module', 'function'], module_name=__name__)
def vagrant_machine_shared(request, env_name, project_path):
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_name')
        if marker:
            env_name = marker.args[0]

    _parts = env_name.split('-')
    os_name = _parts[0]
    env_level = '-'.join(_parts[1:])

    return request.getfixturevalue(
        "vagrant_machine_shared_{}".format(env_fixture_suffix(os_name, env_level))
    )
'''


@pytest.fixture(scope='module')
def post_host_run_hook():
    def f(host, hostname, ssh_config, request):
        pass
    return f


def docker_container(request, docker_client, env_name):
    # TODO API to reuse by other providers
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_name')
        if marker:
            env_name = marker.args[0]

    _parts = env_name.split('-')
    os_name = _parts[0]
    env_level = '-'.join(_parts[1:])

    label = request.fixturename[len('docker_container_{}'.format(request.scope)) + 1:]

    with build_remote(
        'docker', request, os_name, env_level, label
    ) as remote:
        yield remote


def vagrant_machine(localhost, request, tmp_path_factory, env_name):
    # TODO API to reuse by other providers
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_name')
        if marker:
            env_name = marker.args[0]

    _parts = env_name.split('-')
    os_name = _parts[0]
    env_level = '-'.join(_parts[1:])

    label = request.fixturename[len('vagrant_machine_{}'.format(request.scope)) + 1:]

    # TODO configurable way for that
    shared = False
    if shared:
        machine = request.getfixturevalue(
            "vagrant_machine_shared_{}".format(request.scope)
        )
        try:
            # TODO hardcoded
            machine.cmd('snapshot', 'restore', machine.name, 'initial --no-provision')
            yield machine
        finally:
            machine.cmd('halt', '--force')
    else:
        with build_remote(
            'vbox', request, os_name, env_level, label
        ) as remote:
            yield remote


@pytest.fixture(scope='session')
def tmpdir_session(request, tmp_path_factory):
    return tmp_path_factory.getbasetemp()


@pytest.fixture(scope='module')
def tmpdir_module(request, tmp_path_factory):
    return tmp_path_factory.mktemp(safe_filename(request.node.nodeid))


@pytest.fixture
def tmpdir_function(request, tmpdir_module):
    res = tmpdir_module / safe_filename(request.node.name)
    res.mkdir()
    return res


@pytest.fixture
def ssh_config(request, tmpdir_function):
    return tmpdir_function / "ssh_config"


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
def hosts_meta():
    return {}


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
        localhost.check_output(
            "scp -r -F {} {} {}:{}".format(
                ssh_config,
                ' '.join(
                    [
                        str(project_path / path) for path in
                        ('files', 'pillar', 'srv', 'cli')
                    ]
                ),
                hostname,
                PRVSNR_REPO_INSTALL_DIR
            )
        )


@pytest.fixture
def inject_repo(hosts, localhost, project_path, ssh_config, request):
    repo_paths = {}
    target_hosts = list(hosts)

    marker = request.node.get_closest_marker('inject_repo')
    if marker:
        target_hosts = marker.args[0]

    for label, host in hosts.items():
        if label in target_hosts:
            repo_paths[label] = h.inject_repo(localhost, host, ssh_config, project_path)
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
def eos_primary_host_label(eos_hosts):
    return [k for k, v in eos_hosts.items() if v['is_primary']][0]


@pytest.fixture
def eos_primary_host_ip(eos_primary_host_label, hosts_meta):
    meta = hosts_meta[eos_primary_host_label]
    return meta.host.interface(meta.iface).addresses[0]


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


def build_remote(
    envprovider, request, os_name, env_level, label=None
):
    base_name = h.remote_name(
        request.node.nodeid, request.scope, os_name, env_level, label
    )

    # TODO return an object of a class
    if envprovider == 'docker':
        docker_client = request.getfixturevalue('docker_client')
        image = request.getfixturevalue(
            "docker_image_{}".format(env_fixture_suffix(os_name, env_level))
        )
        return _docker_container_run(docker_client, image, base_name)
    elif envprovider == 'vbox':
        box = request.getfixturevalue(
            "vagrant_box_{}".format(env_fixture_suffix(os_name, env_level))
        )
        tmpdir = request.getfixturevalue('tmpdir_{}'.format(request.scope))
        return h._vagrant_machine_up(tmpdir, box, base_name)
    else:
        raise ValueError("unknown envprovider {}".format(envprovider))


def discover_remote(
    request, remote, ssh_config=None, host_fixture_name=None
):
    tmpdir = request.getfixturevalue('tmpdir_{}'.format(request.scope))

    _host = None
    _iface = 'eth0'
    if isinstance(remote, h.Container):
        # update container data
        remote.container.reload()
        _host = testinfra.get_host(remote.container.id, connection='docker')

        #  ssh to be up
        service = _host.service
        #   TODO service name is 'ssh' on debian, ubuntu, ... ???
        service_name = 'sshd'
        while not service(service_name).is_running:
            time.sleep(.5)
        # TODO verify that eth0 is always true for docker
    elif isinstance(remote, h.VagrantMachine):
        # in vagrant ssh-config a machine is accessible via localhost:localport,
        # use that as a temporary way to get its own ip and access
        # its internal ssh port
        _ssh_config_tmp = tmpdir / "ssh_config.{}.tmp".format(remote.name)
        with _ssh_config_tmp.open('w') as f:
            f.write(remote.ssh_config())

        # FIXME sometimes hostonlynetwork of the vbox machine ('eth1' here) is not up properly
        # (route table is not created), no remedy found yet, possible workaround
        # is to remove vbox hostonly network for a machine and re-create the machine
        # https://jts.seagate.com/browse/EOS-3129

        # vagrant uses vagrant machine name as Host ID in ssh-config
        _host = testinfra.get_host(
            "ssh://{}".format(remote.name), ssh_config=str(_ssh_config_tmp)
        )
        _iface = 'eth1'

    else:
        raise ValueError(
            "unexpected remote type: {}".format(type(remote))
        )

    # TODO there might be some cheaper way (e.g. get from testinfra host object)
    _hostname = _host.check_output('hostname')

    if ssh_config is None:
        ssh_config = tmpdir / 'ssh_config.{}'.format(remote.name)
    ssh_config.touch(mode=0o600, exist_ok=True)

    # prepare ssh configuration
    ssh_key = request.getfixturevalue('ssh_key')
    _ssh_config = (
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
            _host.interface(_iface).addresses[0],
            'root',
            str(ssh_key)
        )

    with ssh_config.open('a') as f:
        f.write(_ssh_config)

    hostspec = "ssh://{}".format(_hostname)
    _host = testinfra.get_host(hostspec, ssh_config=str(ssh_config))

    return h.HostMeta(
        remote=remote,
        host=_host,
        ssh_config=ssh_config,
        machine_name=remote.name,
        fixture_name=host_fixture_name,
        hostname=_hostname,
        iface=_iface
    )



def build_host_fixture(label=None, module_name=__name__):
    # TODO not the best way since it should correlate with outside naming policy
    host_fixture_name = '_'.join([part for part in ['host', label] if part])

    remote_fixtures = {'module': {}, 'function': {}}
    for scope in ('module', 'function'):
        remote_fixtures[scope]['docker'] = fixture_builder(
            scope,
            suffix=label,
            module_name=module_name
        )(docker_container)

        remote_fixtures[scope]['vagrant'] = fixture_builder(
            scope,
            suffix=label,
            module_name=module_name
        )(vagrant_machine)

    def host_meta(request):
        label = request.fixturename[len('host_meta_'):]
        _host_fixture_name = 'host' + (('_' + label) if label else '')
        # ensure that related host fixture has been actually called
        host = request.getfixturevalue(_host_fixture_name)
        return request.getfixturevalue('hosts_meta')[_host_fixture_name]

    def hostname(request):
        label = request.fixturename[len('hostname_'):]
        _host_fixture_name = 'host' + (('_' + label) if label else '')
        # ensure that related host fixture has been actually called
        host = request.getfixturevalue(_host_fixture_name)
        hosts_meta = request.getfixturevalue('hosts_meta')
        return hosts_meta[_host_fixture_name].hostname

    def host_tmpdir(request):
        label = request.fixturename[len('host_tmpdir_'):]
        _host_fixture_name = 'host' + (('_' + label) if label else '')
        host = request.getfixturevalue(_host_fixture_name)
        tmpdir_function = request.getfixturevalue('tmpdir_function')
        host.check_output("mkdir -p {}".format(tmpdir_function))
        return tmpdir_function

    def host_rpm_prvsnr(request):
        label = request.fixturename[len('host_rpm_prvsnr_'):]
        suffix = ('_' + label) if label else ''
        _host_fixture_name = 'host' + suffix
        # ensure that related host fixture has been actually called
        host = request.getfixturevalue(_host_fixture_name)
        localhost = request.getfixturevalue('localhost')
        rpm_local_path = request.getfixturevalue('rpm_prvsnr')
        tmpdir = request.getfixturevalue('host_tmpdir' + suffix)
        meta = request.getfixturevalue('host_meta' + suffix)

        rpm_remote_path = tmpdir / rpm_local_path.name
        localhost.check_output(
            "scp -F {} {} {}:{}".format(
                meta.ssh_config,
                rpm_local_path,
                meta.hostname,
                rpm_remote_path
            )
        )
        return rpm_remote_path

    fixture_builder(
        'function',
        suffix=label,
        module_name=module_name,
        name_with_scope=False
    )(host_meta)

    fixture_builder(
        'function',
        suffix=label,
        module_name=module_name,
        name_with_scope=False
    )(hostname)

    fixture_builder(
        'function',
        suffix=label,
        module_name=module_name,
        name_with_scope=False
    )(host_tmpdir)

    fixture_builder(
        'function',
        suffix=label,
        module_name=module_name,
        name_with_scope=False
    )(host_rpm_prvsnr)

    @fixture_builder(
        "function", suffix=label, module_name=module_name,
        name_with_scope=False
    )
    def host(localhost, request, tmpdir_function, hosts_meta):
        envprovider = request.config.getoption("envprovider")
        if envprovider == 'host':
            return localhost

        scope = (
            'function' if request.node.get_closest_marker('isolated')
            else 'module'
        )

        ssh_config = request.getfixturevalue('ssh_config')

        if envprovider == 'docker':
            remote = request.getfixturevalue(
                remote_fixtures[scope]['docker'].__name__
            )
        else:
            # TODO skip if vagrant or packer or virtualbox is not installed
            # pytest.skip()
            remote = request.getfixturevalue(
                remote_fixtures[scope]['vagrant'].__name__
            )

        meta = discover_remote(
            request, remote,
            ssh_config=ssh_config, host_fixture_name=host_fixture_name
        )

        hosts_meta[host_fixture_name] = meta

        # TODO add try-catch and remove default implementation of post_host_run_hook
        request.getfixturevalue('post_host_run_hook')(
            meta.host, meta.hostname, ssh_config, request
        )

        return meta.host


# default 'host' fixture is always present
build_host_fixture()
# also host fixtures for EOS stack makes sense
build_host_fixture('eosnode1')
build_host_fixture('eosnode2')
