import docker
import time
import json
import attr
import os
from pathlib import Path
from collections import defaultdict

import pytest
import testinfra

import logging

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

# TODO check packer is available
@attr.s
class Packer(object):
    packerfile = attr.ib(
        converter=lambda v: v.resolve()
    )
    log = attr.ib(default=True)
    _localhost = attr.ib(
        init=False, default=testinfra.get_host('local://')
    )

    @packerfile.validator
    def _check_packerfile(self, attribute, value):
        if not value.is_file:
            raise ValueError(
                "{} is not a file".format(value)
            )
        self.validate()

    def check_output(self, cmd):
        res = None
        try:
            res = self._localhost.run(cmd)
            assert res.rc == 0
        finally:
            if res is not None:
                for line in res.stdout.split(os.linesep):
                    logger.debug(line)
        return res.stdout

    def packer(self, command, *args):
        return self.check_output(
            "{}packer {} {} {}".format(
                "PACKER_LOG=1 " if self.log else '',
                command,
                ' '.join([*args]), self.packerfile
            )
        )

    # TODO use some dynamic way instead
    def build(self, *args):
        return self.packer("build", *args)

    def validate(self, *args):
        return self.packer("validate", *args)


# TODO check packer is available
@attr.s
class Vagrant(object):
    # TODO validate
    env_vars = attr.ib(default=None)
    log = attr.ib(default='debug')
    _env_prefix = attr.ib(default='')
    _localhost = attr.ib(
        init=False,
        default=testinfra.get_host('local://')
    )

    def __attrs_post_init__(self):
        if self.env_vars is not None:
            self._env_prefix = ' '.join(
                ["{}={}".format(n, v) for (n, v) in self.env_vars]
            ) + ' '

    def check_output(self, cmd):
        res = None
        try:
            res = self._localhost.run(self._env_prefix + cmd)
            assert res.rc == 0
        finally:
            if res is not None:
                for line in res.stdout.split(os.linesep):
                    logger.debug(line)
        return res.stdout

    def vagrant(self, command, *args):
        return self.check_output(
            "{}vagrant {} {}".format(
                "VAGRANT_LOG={} ".format(self.log) if self.log else '',
                command,
                ' '.join([*args])
            )
        )

    # TODO use some dynamic way instead
    def ssh(self, *args):
        return self.vagrant("ssh --", *args)

    def ssh_config(self, *args):
        return self.vagrant("ssh-config", *args)

    def validate(self, *args):
        return self.vagrant("validate", *args)

    def up(self, *args):
        return self.vagrant("up", *args)

    def destroy(self, *args):
        return self.vagrant("destroy", *args)

    def box(self, *args):
        return self.vagrant("box", *args)

    def cmd(self, cmd, *args):
        return self.vagrant(cmd, *args)


# TODO check vagrant is available
@attr.s
class VagrantMachine(object):

    VAGRANTFILE_TMPL = (
        "Vagrant.configure('2') do |config|\n"
        "  config.vm.box = '{0}'\n"
        "  config.vm.box_check_update = false\n"
        "  config.vm.define '{1}'\n"
        "  config.vm.hostname = '{2}'\n"
        "  config.vm.provider :virtualbox do |vb, override|\n"
        "    vb.name = '{1}'\n"
        "  end\n"
        "end\n"
    )

    # TODO validators for all
    name = attr.ib()
    box = attr.ib()
    vagrantfile = attr.ib(
        converter=lambda v: None if v is None else v.resolve(),
        default=None
    )
    vagrantfile_path = attr.ib(
        converter=lambda v: None if v is None else Path(v),
        default=None
    )
    vagrantfile_tmpl = attr.ib(
        default=VAGRANTFILE_TMPL
    )
    hostname = attr.ib(
        converter=lambda v: None if v is None else safe_hostname(v),
        default=None
    )
    log = attr.ib(default='debug')
    _vagrant = attr.ib(
        init=False,
        default=None
    )
    _localhost = attr.ib(
        init=False,
        default=testinfra.get_host('local://')
    )

    @vagrantfile.validator
    def _check_vagrantfile(self, attribute, value):
        if value is None:
            if self.vagrantfile_path is None:
                raise ValueError(
                    "Either vagrantfile or vagrantfile_path should be defined"
                )
            else:
                return
        if not value.is_file:
            raise ValueError(
                "{} is not a file".format(value)
            )
        # TODO here __attrs_post_init__ hasn't been called yet
        # self.validate()
        self._localhost.check_output(
            "VAGRANT_CWD={} VAGRANT_VAGRANTFILE={} vagrant validate"
            .format(value.parent, value.name)
        )

    @vagrantfile_path.validator
    def _check_vagrantfile_path(self, attribute, value):
        if value is None:
            return
        value.touch()

    def __attrs_post_init__(self):
        if self.hostname is None:
            self.hostname = safe_hostname(self.name)

        # create vagrantfile if missed using template
        if self.vagrantfile is None:
            self.vagrantfile = self.vagrantfile_path
            _content = self.vagrantfile_tmpl.format(
                self.box.name, self.name, self.hostname
            )
            self.vagrantfile.write_text(_content)

        self._vagrant = Vagrant(
            log=self.log, env_vars=[
                ('VAGRANT_CWD', self.vagrantfile.parent),
                ('VAGRANT_VAGRANTFILE', self.vagrantfile.name)
            ]
        )

    # TODO use some dynamic way instead
    def ssh(self, *args):
        return self._vagrant.ssh(*args)

    def ssh_config(self, *args):
        return self._vagrant.ssh_config(*args)

    def validate(self, *args):
        return self._vagrant.validate(*args)

    def up(self, *args):
        return self._vagrant.up(*args)

    def destroy(self, *args):
        return self._vagrant.destroy(*args)

    def cmd(self, cmd, *args):
        return self._vagrant.cmd(cmd, *args)


@attr.s
class VagrantBox(object):
    name = attr.ib()
    path = attr.ib(
        converter=lambda v: v.resolve()
    )
    @path.validator
    def _check_path(self, attribute, value):
        if not value.is_file:
            raise ValueError(
                "{} is not a file".format(value)
            )


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


@fixture_builder(['module', 'function'], module_name=__name__)
def docker_image(request, docker_client, env_name, project_path):
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_name')
        if marker:
            env_name = marker.args[0]

    _parts = env_name.split('-')
    os_name = _parts[0]
    env_level = '-'.join(_parts[1:])

    return request.getfixturevalue(
        "docker_image_{}".format(env_fixture_suffix(os_name, env_level))
    )


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
        if not box_path.exists:
            # TODO pytest options to turn on packer debug
            # TODO add box to vagrant here: it should prevent auto add by
            #      vagrant during 'vagrant up' where it uses path to source box
            packer = Packer(packerfile)
            packer.build('--force')

        box = VagrantBox(
            "{}.{}".format(DOCKER_IMAGES_REPO.replace('/', '.'), _env_name),
            box_path
        )
        Vagrant(log='debug').box(
            "add --force --provider virtualbox --name",
            box.name,
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


@fixture_builder(['module', 'function'], module_name=__name__)
def vagrant_box(request, env_name, project_path):
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_name')
        if marker:
            env_name = marker.args[0]

    _parts = env_name.split('-')
    os_name = _parts[0]
    env_level = '-'.join(_parts[1:])

    return request.getfixturevalue(
        "vagrant_box_{}".format(env_fixture_suffix(os_name, env_level))
    )


def build_vagrant_machine_shared_fixture(os_name, env_level):

    def vagrant_machine_shared(request, project_path, tmp_path_factory):
        box = request.getfixturevalue(
            "vagrant_box_{}".format(
                env_fixture_suffix(os_name, env_level))
        )
        machine_name = safe_vagrant_machine_name("{}-shared".format(box.name))
        tmpdir = tmp_path_factory.mktemp(safe_filename(machine_name))
        vagrantfile_path = str(tmpdir / 'Vagrantfile')
        machine = VagrantMachine(
            machine_name, box=box, vagrantfile_path=vagrantfile_path
        )
        try:
            machine.destroy('--force')
            machine.up()
            machine.cmd('halt')
            # TODO hardcoded
            machine.cmd('snapshot', 'save initial --force')
            machine.cmd('halt --force')
            yield machine
        finally:
            machine.destroy("--force")

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


@pytest.fixture(scope='module')
def post_host_run_hook():
    def f(host, hostname, ssh_config, request):
        pass
    return f


def docker_container(request, docker_client):
    try:
        suffix = request.fixturename.split('docker_container')[1]
    except IndexError:
        suffix = None

    container_name = "{}{}".format(safe_docker_container_name(request.node.nodeid), suffix)

    image = request.getfixturevalue("docker_image_{}".format(request.scope))
    try:
        container = _docker_container_run(docker_client, image, container_name)
        yield container
    finally:
        try:
            # 'container' might be not assigned yet here
            _container = docker_client.containers.get(container_name)
        except Exception:
            # container with the name might not be even created yet
            pass
        else:
            _container.remove(force=True)


def vagrant_machine(localhost, request, tmp_path_factory):
    try:
        suffix = request.fixturename.split('vagrant_machine')[1]
    except IndexError:
        suffix = None

    # TODO configurable way for that
    shared = True
    if shared:
        machine = request.getfixturevalue(
            "vagrant_machine_shared_{}".format(request.scope)
        )
        try:
            # TODO hardcoded
            machine.cmd('snapshot', 'restore initial --no-provision')
            yield machine
        finally:
            machine.cmd('halt', '--force')
    else:
        box = request.getfixturevalue("vagrant_box_{}".format(request.scope))
        machine_name = "{}{}".format(safe_vagrant_machine_name(request.node.nodeid), suffix)
        tmpdir = tmp_path_factory.mktemp(safe_filename(request.node.nodeid))
        vagrantfile_path = str(tmpdir / 'Vagrantfile.{}'.format(box.name))
        machine = VagrantMachine(
            machine_name, box=box, vagrantfile_path=vagrantfile_path
        )
        try:
            machine.up()
            yield machine
        finally:
            if machine:
                machine.destroy("--force")


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
def install_provisioner(hosts, localhost, project_path, ssh_config):
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
    host_repo_dir = Path('/tmp') / project_path.name
    target_hosts = list(hosts)

    marker = request.node.get_closest_marker('inject_repo')
    if marker:
        target_hosts = marker.args[0]

    for label, host in hosts.items():
        if label in target_hosts:
            hostname = host.check_output('hostname')
            host.check_output("mkdir -p {}".format(host_repo_dir))
            # TODO smarter way, option:
            # - copy just .git and everything that modified
            # - do remote git commit
            # ! we need modifications to be taken into account
            # by possible 'git archive' command
            # !? deleted / not yet added files
            localhost.check_output(
                "scp -r -F {} {} {}:{}".format(
                    ssh_config,
                    ' '.join(
                        [
                            str(project_path / path) for path in
                            ('.git', 'files', 'pillar', 'srv', 'cli')
                        ]
                    ),
                    hostname,
                    host_repo_dir
                )
            )
            repo_paths[label] = host_repo_dir
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
def configure_salt(eos_hosts, install_provisioner, eos_primary_host_ip):
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
def accept_salt_keys(eos_hosts, install_provisioner, eos_primary_host):
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

    vagrant_machine_fixtures = {
        scope: fixture_builder(
            scope,
            suffix=suffix,
            module_name=module_name
        )(vagrant_machine) for scope in ('module', 'function')
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

        scope = (
            'function' if request.node.get_closest_marker('isolated')
            else 'module'
        )

        _hostname = None
        _ssh_config = None

        # TODO add try-catch and remove default implementation of post_host_run_hook
        post_host_run_hook = request.getfixturevalue('post_host_run_hook')
        ssh_config = request.getfixturevalue('ssh_config')
        ssh_config.touch(mode=0o600, exist_ok=True)

        if envprovider == 'docker':
            container = request.getfixturevalue(
                docker_container_fixtures[scope].__name__
            )
            # update container data
            container.reload()

            _host = testinfra.get_host(container.id, connection='docker')
            # TODO there might be some cheaper way (e.g. get from testinfra host object)
            _hostname = _host.check_output('hostname')

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
                    _host.interface("eth0").addresses[0],
                    'root',
                    str(ssh_key)
                )

            # Wait ssh to be up
            service = _host.service
            #   TODO service name is 'ssh' on debian, ubuntu, ... ???
            service_name = 'sshd'
            while not service(service_name).is_running:
                time.sleep(.5)

        else:
            # TODO skip if vagrant or packer or virtualbox is not installed
            # pytest.skip()
            machine = request.getfixturevalue(
                vagrant_machine_fixtures[scope].__name__
            )
            _hostname = machine.hostname
            _ssh_config = machine.ssh_config()
            # vagrant uses vagrant machine name as Host ID in ssh-config,
            # replace it with hostname which is seems safer and satisfies
            # these tests convention
            _ssh_config = _ssh_config.replace(
                "Host {}\n".format(
                    machine.name
                ), "Host {}\n".format(
                    machine.hostname
                )
            )

        with ssh_config.open('a') as f:
            f.write(_ssh_config)

        hostspec = "ssh://{}".format(_hostname)
        _host = testinfra.get_host(hostspec, ssh_config=str(ssh_config))
        post_host_run_hook(_host, _hostname, ssh_config, request)

        return _host


# default 'host' fixture is always present
build_host_fixture()
# also host fixtures for EOS stack makes sense
build_host_fixture('eosnode1')
build_host_fixture('eosnode2')
