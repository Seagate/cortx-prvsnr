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

import sys
import docker
import time
import json
from importlib import import_module
from typing import Type
from pathlib import Path
from collections import defaultdict

import pytest
import testinfra

import logging

from provisioner import inputs
import test.helper as h
from .helper import (
    fixture_builder,
    safe_filename,
    PRVSNR_REPO_INSTALL_DIR, mock_system_cmd, restore_system_cmd
)

from . import testapi
from .testapi.integration import HostMeta

mod = sys.modules[__name__]

# Note. Just to make that explicit and lint tools happy
for fixture in testapi.fixtures:
    setattr(mod, fixture.__name__, fixture)

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent

DOCKER_IMAGES_REPO = "seagate/cortx-prvsnr"
VAGRANT_VMS_PREFIX = DOCKER_IMAGES_REPO.replace('/', '.')

SSH_KEY_FILE_NAME = "id_rsa.test"
MAX_NODES_NUMBER = 6

# TODO 'base' level format is too different
ENV_LEVELS_HIERARCHY = {
    'base': {
        'centos7.5.1804': {
            'docker': 'centos:7.5.1804',
            'vagrant': {
                'vm_box_name': 'geerlingguy/centos7',
                'vm_box_version': '1.2.7'
            }
        },
        'centos7.7.1908': {
            'docker': 'centos:7.7.1908',
            'vagrant': {
                'vm_box_name': 'geerlingguy/centos7',
                'vm_box_version': '1.2.17'
            }
        },
        'centos7.8.2003': {
            'docker': 'centos:7.8.2003'
        },
        'centos8.2.2004': {
            'docker': 'centos:8.2.2004'
        }
    },
    'repos-installed': 'base',
    'salt-installed': 'repos-installed',
    'rsyslog-installed': 'salt-installed',
    'singlenode-prvsnr-installed': {
        'parent': 'salt-installed',
        'docker': {
            'build_type': 'commit',
            'scripts': [
                "cd {repo_path}/cli/src && bash ../../images/vagrant/setup_prvsnr_singlenode.sh local ''",  # noqa: E501
                "cd {repo_path}/cli/src && bash ../../images/vagrant/setup_prvsnr_api_env.sh",  # noqa: E501
                "rm -rf {repo_path}"
            ]
        }
    },
    'singlenode-test-integration-ready': 'singlenode-prvsnr-installed',
    # only for vbox
    'singlenode-deploy-ready': {
        'parent': 'salt-installed',
        'vars': ['prvsnr_src', 'prvsnr_release', 'cortx_release']
    },
    'singlenode-cortx-deployed': 'singlenode-deploy-ready',
    'singlenode-cortx-ready': 'singlenode-cortx-deployed',

    # utility levels
    'rpmbuild': 'base',
    'fpm': 'base',
    'utils': 'base',
    'setup': 'utils',
    'network-manager-installed': 'base',

    # bvt
    'singlenode-bvt-ready': {
        'parent': 'base',
        'vars': ['prvsnr_cli_release', 'prvsnr_release', 'cortx_release']
    }
}


BASE_OS_NAMES = list(ENV_LEVELS_HIERARCHY['base'])
ENV_LEVELS = list(ENV_LEVELS_HIERARCHY)
DEFAULT_BASE_OS_NAME = 'centos7.8.2003'

DEFAULT_CLUSTER_SPEC = {
    f'srvnode{node_id}': {
        'hostname': f'srvnode-{node_id}',
        'minion_id': f'srvnode-{node_id}',
        'roles': ['primary' if node_id == 1 else 'secondary'],
    } for node_id in range(1, MAX_NODES_NUMBER + 1)
}


class LocalHostMeta(HostMeta):
    @property
    def hostname(self):
        return 'localhost'

    @property
    def tmpdir(self):
        if self._tmpdir is None:
            self._tmpdir = self.request.getfixturevalue('tmpdir_function')
        return self._tmpdir

    @property
    def rpm_prvsnr(self):
        if self._rpm_prvsnr is None:
            self._rpm_prvsnr = self.request.getfixturevalue('rpm_prvsnr')
        return self._rpm_prvsnr

    @property
    def rpm_prvsnr_cli(self):
        if self._rpm_prvsnr is None:
            self._rpm_prvsnr = self.request.getfixturevalue('rpm_prvsnr_cli')
        return self._rpm_prvsnr

    @property
    def repo(self):
        if self._repo is None:
            self._repo = h.PROJECT_PATH
        return self._repo

    @property
    def fixture_name(self):
        return 'mlocalhost'


def _add_testing_levels_markers(config):
    for level in h.LevelT:
        config.addinivalue_line(
            "markers",
            f"{level.value}: mark test as a scenario"
            f" with '{level.value}' level"
        )


def _add_testing_topics_markers(config):
    for topic in h.TopicT:
        config.addinivalue_line(
            "markers",
            f"{topic.value}: mark test as a scenario"
            f" belongs to '{topic.value}' topic"
        )


def pytest_configure(config):
    _add_testing_levels_markers(config)

    _add_testing_topics_markers(config)

    config.addinivalue_line(
        "markers", "debug: mark test as a one for debug"
    )
    config.addinivalue_line(
        "markers", "example: mark test as an example"
    )
    config.addinivalue_line(
        "markers", "outdated: mark test as an outdated (would be skipped)"
    )
    config.addinivalue_line(
        "markers", "verified: mark test as verified (up-to-date) one"
    )

    config.addinivalue_line(
        "markers", "env_provider(string): mark test to be run "
                   "in the environment provided by the provider"
    )
    config.addinivalue_line(
        "markers", "env_level(string): mark test to be run "
                   "in the specific environment level"
    )
    config.addinivalue_line(
        "markers", "cortx_spec(dict): mark test as expecting "
                   "specific CORTX stack configuration, default: {}"
                   .format(json.dumps(DEFAULT_CLUSTER_SPEC))
    )
    config.addinivalue_line(
        "markers", "hosts(list): mark test as expecting "
                   "the specified list of hosts by labels, "
                   "default: ['']"
    )
    config.addinivalue_line(
        "markers", "hosts_num: mark test as expecting "
                   "the specified number of hosts"
                   "default: undefined"
    )
    config.addinivalue_line(
        "markers", "isolated: mark test to be run in the isolated "
                   "environment instead of module wide shared"
    )
    config.addinivalue_line(
        "markers", "inject_ssh_config: mark test as expecting ssh "
                   "configuration only for specified hosts, "
                   "default: all hosts"
    )
    config.addinivalue_line(
        "markers", "mock_cmds(dict[host_lable, list]): mark test as requiring "
                   "list of mocked system commands per host"
    )
    config.addinivalue_line(
        "markers", "vagrant_default_ssh(string): mark test to use "
                   "default ssh config provided by vagrant, "
                   "default: True for single node env, False otherwise"
    )
    config.addinivalue_line(
        "markers", "cortx_bvt: mark test as BVT one"
    )
    config.addinivalue_line(
        "markers", "patch_logging: mark test as expected patched logging"
    )
    config.addinivalue_line(
        "markers", "verifies: mark test as verifying specified issues"
    )


prvsnr_pytest_options = {
    # TODO might be useful to test in multiple at once
    "base-env": dict(
        action='store', choices=BASE_OS_NAMES,
        default=DEFAULT_BASE_OS_NAME,
        help="base OS name, defaults to {}".format(DEFAULT_BASE_OS_NAME)
    ),
    "env-provider": dict(
        action='store',
        choices=['host', 'docker', 'vbox'],
        default='docker',
        help="test environment provider, defaults to docker"
    ),
    "env-level": dict(
        action='store',
        choices=ENV_LEVELS,
        default=None,
        help="test environment level"
    ),
    "prvsnr-src": dict(
        action='store', choices=['rpm', 'github', 'local'],
        default='rpm',
        help="Provisioner source to use, defaults to 'rpm'"
    ),
    # XXX outdated options (bvt scope)
    #    "prvsnr-cli-release": dict(
    #        action='store',
    #        default='integration/centos-7.7.1908/last_successful',
    #        help=(
    #            "Provisioner cli release to use, "
    #            "defaults to 'integration/centos-7.7.1908/last_successful'"
    #        )
    #    ),
    #    "prvsnr-release": dict(
    #        action='store',
    #        default='integration/centos-7.7.1908/last_successful',
    #        help=(
    #            "Provisioner release to use, "
    #            "defaults to 'integration/centos-7.7.1908/last_successful'"
    #        )
    #    ),
    #    "cortx-release": dict(
    #        action='store',
    #        default='integration/centos-7.7.1908/last_successful',
    #        help=(
    #            "Target release to verify, "
    #            "defaults to 'integration/centos-7.7.1908/last_successful'"
    #        )
    #    )
}


def pytest_addoption(parser):
    # TODO find a way when inner module can do that itself
    #      (currently pytest_addoption is called before any imports
    #       of low level test modules)
    setup_opts_module = import_module(
        'test.api.python.integration.setup.conftest'
    )

    h.add_options(parser, prvsnr_pytest_options)
    h.add_options(
        parser, setup_opts_module.SetupOpts.prepare_args()
    )


# TODO DOC how to modify tests collections
# TODO DOC how to apply markers dynamically so it would impact collection
def pytest_collection_modifyitems(session, config, items):
    for item in items:
        for level in h.LevelT:
            if level.value in item.fixturenames:
                item.add_marker(getattr(pytest.mark, level.value))
                break
        else:
            item.add_marker(getattr(pytest.mark, h.LevelT.NOLEVEL.value))

        for topic in h.TopicT:
            if topic.value in item.fixturenames:
                item.add_marker(getattr(pytest.mark, topic.value))
                break
        else:
            item.add_marker(getattr(pytest.mark, h.TopicT.NOTOPIC.value))

        if 'any_level' in item.fixturenames:
            item.add_marker(
                getattr(pytest.mark, item.callspec.params['any_level'].value)
            )

        if 'any_topic' in item.fixturenames:
            item.add_marker(
                getattr(pytest.mark, item.callspec.params['any_topic'].value)
            )

        for marker in ('debug', 'outdated', 'example'):
            if item.get_closest_marker(marker):
                item.add_marker(pytest.mark.skip)


for level in list(h.LevelT) + list(h.TopicT):
    fixture_builder(
        'session', name_with_scope=False, module_name=__name__,
        fixture_name=level.value
    )(lambda: None)


@pytest.fixture(scope='session')
def get_fixture(request):
    def _f(fixture_name):
        return request.getfixturevalue(fixture_name)
    return _f


@pytest.fixture(scope='session')
def custom_opts_t():
    return inputs.ParserMixin


@pytest.fixture(scope='session')
def custom_opts(request, custom_opts_t: Type[inputs.ParserMixin]):
    return custom_opts_t.from_args(request.config.option)


@pytest.fixture(scope="session")
def run_options(custom_opts_t: Type[inputs.ParserMixin]):
    return list(prvsnr_pytest_options) + list(custom_opts_t.parser_args())


@pytest.fixture(scope="session", autouse=True)
def dump_options(request, run_options):
    h.dump_options(request, run_options)


@pytest.fixture(scope="session")
def project_path():
    return h.PROJECT_PATH


@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()


@pytest.fixture(scope="session")
def localhost():
    return h.localhost


@pytest.fixture(scope="session")
def local_user_id(localhost):
    return h.localhost.check_output('id -u')


@pytest.fixture(scope="session")
def local_user_name(localhost):
    return 'user'


@pytest.fixture(scope='session')
def ssh_key(tmpdir_session):
    bundled_key = MODULE_DIR / SSH_KEY_FILE_NAME
    res = tmpdir_session / SSH_KEY_FILE_NAME
    res.write_text(bundled_key.read_text())
    res.chmod(0o600)
    res.with_name(f"{res.name}.pub").write_text(
        bundled_key.with_name(f"{bundled_key.name}.pub").read_text()
    )
    return res


@pytest.fixture(scope="session")
def vagrant_global_status_prune(localhost):
    localhost.check_output('vagrant global-status --prune')


@pytest.fixture(scope="session")
def base_env(request):
    return request.config.getoption("base_env")


@pytest.fixture(scope='session')
def ask_proceed():

    def _f():
        input('Press any key to continue...')

    return _f


@pytest.fixture(scope='session', params=h.LevelT)
def any_level(request):
    return request.param


@pytest.fixture(scope='session', params=h.TopicT)
def any_topic(request):
    return request.param


@pytest.fixture
def env_provider(request):
    res = request.config.getoption("env_provider")
    marker = request.node.get_closest_marker('env_provider')
    if marker:
        res = marker.args[0]
    return res


@pytest.fixture
def patch_logging(request, monkeypatch):
    marker = request.node.get_closest_marker('patch_logging')
    if marker:
        res = marker.args[0]
    else:
        return

    for module, levels in res:
        for log_f in levels:
            monkeypatch.setattr(
                getattr(module, 'logger'), log_f, lambda *args, **kwargs: None
            )


@pytest.fixture(scope='session')
def hosts_spec(request):
    return {
        f'srvnode{node_id}': {
            'remote': {
                'hostname': f'srvnode-{node_id}',
                'specific': {
                    'vbox': {
                        'memory': 4096,
                        'cpus': 2,
                        'mgmt_disk_size': 2048,
                        'data_disk_size': 2048
                    }
                }
            },
            'minion_id': f'srvnode-{node_id}',
            'roles': ['primary' if node_id == 1 else 'secondary'],
        } for node_id in range(1, MAX_NODES_NUMBER + 1)
    }


# TODO multi platforms case
@pytest.fixture(scope="session")
def vbox_seed_machine(
    request, base_env, project_path, vagrant_global_status_prune
):
    env_spec = ENV_LEVELS_HIERARCHY['base'][base_env]['vagrant']
    # TODO separator ???
    machine_name = '_'.join([VAGRANT_VMS_PREFIX, base_env, 'seed'])
    vagrantfile_name = "Vagrantfile.seed"
    vagrantfile = project_path / 'images' / 'vagrant' / vagrantfile_name

    machine = h.VagrantMachine(
        machine_name, vagrantfile=vagrantfile, user_vars={
            'VAR_VM_NAME': machine_name,
            'VAR_VM_BOX_NAME': env_spec['vm_box_name'],
            'VAR_VM_BOX_VERSION': env_spec['vm_box_version']
        }
    )

    logger.info(
        "Preparing VirtualBox {} seed machine"
        .format(base_env)
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

    return machine


# TODO
#  - DOCS
#  - make configurable to use specific git state (git archive)
@pytest.fixture(scope='session')
def repo_tgz(project_path, localhost, tmpdir_session):
    res = tmpdir_session / 'repo.tgz'
    excluded_dirs = ['--exclude="{}"'.format(d) for d in h.REPO_BUILD_DIRS]
    localhost.check_output(
        'tar -czf "{}" {} -C "{}" .'
        .format(res, ' '.join(excluded_dirs), project_path)
    )
    return res


def _rpmbuild_mhost(
    request, env_provider=None, base_env=None, label=None
):
    if not env_provider:
        env_provider = request.config.getoption("env_provider")

    if not base_env:
        base_env = request.config.getoption("base_env")

    if not label:
        label = 'rpmbuild'

    # TODO DOCS : example how to run machine out of fixture scope
    remote = build_remote(
        env_provider, request, base_env, label
    )

    try:
        return discover_remote(request, remote)
    except Exception:
        remote.destroy()
        raise


def _copy_to_local(mhost, host_path, tmpdir_local):
    local_path = tmpdir_local / host_path.name
    h.localhost.check_output(
        "scp -r -F {} {}:{} {}".format(
            mhost.ssh_config,
            mhost.hostname,
            host_path,
            local_path
        )
    )
    return local_path


def rpm_prvsnr_build(mhost, version=None, release_number=None):
    cmd = ['devops/rpms/buildrpm.sh']
    if version:
        cmd.extend(['-e', str(version)])
    if release_number:
        cmd.extend(['-b', str(release_number)])

    mhost.check_output(
        'cd {} && sh -x {}'.format(mhost.repo, ' '.join(cmd))
    )
    return Path(
        mhost.check_output(
            'ls ~/rpmbuild/RPMS/x86_64/{}*.rpm | grep -v debug'
            .format(h.PRVSNR_PKG_NAME)
        )
    )


def rpm_prvsnr_cli_build(mhost, version=None, release_number=None):
    # TODO IMPROVE DRY
    cmd = ['cli/buildrpm.sh']
    if version:
        cmd.extend(['-e', str(version)])
    if release_number:
        cmd.extend(['-b', str(release_number)])

    mhost.check_output(
        'cd {} && sh -x {}'.format(mhost.repo, ' '.join(cmd))
    )
    return Path(
        mhost.check_output(
            'ls ~/rpmbuild/RPMS/x86_64/{}*.rpm | grep -v debug'
            .format(h.PRVSNR_CLI_PKG_NAME)
        )
    )


def rpm_prvsnr_api_build(mhost, pkg_version=None):
    build_dir = 'rpmbuild'
    cmd = [
        'devops/rpms/api/build_python_api.sh',
        '--out-dir', build_dir,
        '--out-type', 'rpm'
    ]

    if pkg_version:
        cmd += ['--pkg-ver', pkg_version]

    mhost.check_output(
        'cd {0} && rm -rf {1} && mkdir {1} && sh -x {2}'
        .format(mhost.repo, build_dir, ' '.join(cmd))
    )
    return Path(
        mhost.check_output(
            'ls {}/*.rpm | grep -v debug'
            .format(mhost.repo / build_dir)
        )
    )


@pytest.fixture(scope='session')
def rpm_build():
    def _f(
        request, tmpdir_local,
        rpm_type='core', mhost_init_cb=None,
        **kwargs
    ):
        if rpm_type not in ('core', 'cli', 'api'):
            raise ValueError(rpm_type)

        if rpm_type == 'api':
            env_provider = 'docker'
            base_env = 'centos8.2.2004'
            label = 'fpm'
        else:
            env_provider = None
            base_env = None
            label = None

        mhost = _rpmbuild_mhost(
            request, env_provider=env_provider, base_env=base_env, label=label
        )
        # TODO DOCS : example how to run machine out of fixture scope
        with mhost.remote as _:
            if mhost_init_cb:
                mhost_init_cb(mhost)
            rpm_remote_path = (
                rpm_prvsnr_cli_build(mhost, **kwargs) if rpm_type == 'cli'
                else rpm_prvsnr_build(mhost, **kwargs) if rpm_type == 'core'
                else rpm_prvsnr_api_build(mhost, **kwargs)
            )
            return _copy_to_local(
                mhost, rpm_remote_path, tmpdir_local
            )
    return _f


@pytest.fixture(scope='session')
def rpm_prvsnr(request, tmpdir_session, rpm_build):
    return rpm_build(request, tmpdir_session, rpm_type='core')


@pytest.fixture(scope='session')
def rpm_prvsnr_cli(request, tmpdir_session, rpm_build):
    return rpm_build(request, tmpdir_session, rpm_type='cli')


@pytest.fixture(scope='session')
def rpm_prvsnr_api(request, tmpdir_session, rpm_build):
    return rpm_build(request, tmpdir_session, rpm_type='api')


@pytest.fixture(autouse=True)
def log_test_name(request):
    logger.debug('Test started: {}'.format(request.node.nodeid))
    yield
    logger.debug('Test finished: {}'.format(request.node.nodeid))


@pytest.fixture(scope='module')
def env_level():
    return 'base'


def env_fixture_suffix(os_name, env_level):
    return "{}_{}".format(os_name, env_level.replace('-', '_'))


def build_docker_image_fixture(os_name, env_level):  # noqa: C901 FIXME

    def docker_image(request, docker_client, project_path, tmpdir_session):
        env_spec = ENV_LEVELS_HIERARCHY[env_level]
        docker_spec = {}
        build_type = 'dockerfile'

        if env_level == 'base':
            parent_env_level = None
        elif type(env_spec) is dict:
            parent_env_level = env_spec['parent']
            docker_spec = env_spec.get('docker', {})
            build_type = docker_spec.get('build_type', 'dockerfile')
        else:
            parent_env_level = env_spec

        def _image_short_id(image):
            return image.short_id.replace('sha256:', '')

        def _image_tag(image, os_name, env_level):
            # TODO better parts separator
            return '-'.join([os_name, env_level, _image_short_id(image)])

        def _image_name(image, os_name, env_level):
            return (
                "{}:{}".format(
                    DOCKER_IMAGES_REPO, _image_tag(image, os_name, env_level)
                )
            )

        def _parent_image_name():
            if env_level == 'base':
                # TODO image object would be necessary for 'commit' built_type
                return env_spec[os_name]['docker'], None
            else:
                p_image = request.getfixturevalue(
                    "docker_image_{}".format(
                        env_fixture_suffix(os_name, parent_env_level)
                    )
                )
                p_image_name = _image_name(p_image, os_name, parent_env_level)
                if p_image_name not in p_image.tags:
                    logger.warning(
                        "parent image {} doesn't have expected tag {}"
                        .format(p_image, p_image_name)
                    )
                    # TODO what if no tags at all,
                    #      do we allow referencing by id ?
                    p_image_name = p_image.tags[0]
                return p_image_name, p_image

        parent_image_name, parent_image = _parent_image_name()

        # build image
        logger.info(
            "Building docker env '{}' for base env '{}'"
            .format(env_level, os_name)
        )
        if build_type == 'dockerfile':
            df_name = "Dockerfile.{}".format(env_level)
            dockerfile = project_path / 'images' / 'docker' / df_name
            dockerfile_tmpl = dockerfile.parent / (dockerfile.name + '.tmpl')

            if dockerfile_tmpl.exists():
                dockerfile_str = dockerfile_tmpl.read_text().format(
                    parent=parent_image_name
                )
            else:
                dockerfile_str = dockerfile.read_text()

            dockerfile = tmpdir_session / dockerfile.name
            dockerfile.write_text(dockerfile_str)
            image = h._docker_image_build(
                docker_client, dockerfile, ctx=project_path
            )
        else:  # image as container commit
            assert parent_image is not None
            remote = build_remote(
                'docker',
                request,
                os_name,
                env_level=parent_env_level,
                base_level=parent_image
            )

            try:
                mhost = discover_remote(request, remote)
            except Exception:
                remote.destroy()
                raise

            with mhost.remote as _:
                # apply scripts to running container
                for script in docker_spec.get('scripts', []):
                    mhost.check_output(script.format(repo_path=mhost.repo))
                # commit it to image
                image = h._docker_container_commit(remote)

        # set image name
        if _image_name(image, os_name, env_level) not in image.tags:
            try:
                image.tag(DOCKER_IMAGES_REPO, tag=_image_tag(
                    image, os_name, env_level
                ))
            except Exception:
                # ensure that image doesn't have any other tags
                # TODO what if it actually was tagged but failed then,
                #      is it possible in docker API
                if not image.tags:
                    docker_client.images.remove(
                        image.id, force=False, noprune=False
                    )
                raise
            else:
                image.reload()

        return image

    fixture_builder(
        'session',
        suffix=('_' + env_fixture_suffix(os_name, env_level)),
        module_name=__name__,
        name_with_scope=False
    )(docker_image)


for _os_name in BASE_OS_NAMES:
    for _env_level in ENV_LEVELS_HIERARCHY:
        build_docker_image_fixture(_os_name, _env_level)


def build_vagrant_box_fixture(os_name, env_level):  # noqa: C901 FIXME

    # returns VagrantBox object, box is already added to vagrant
    def vagrant_box(request, base_env, project_path):

        def _get_user_vars():
            res = {'base_env': base_env}

            if env_level == 'base':
                p_machine = request.getfixturevalue('vbox_seed_machine')
                res['seed_vm_name'] = p_machine.name
            else:
                env_spec = ENV_LEVELS_HIERARCHY[env_level]
                if type(env_spec) is dict:
                    p_env = env_spec['parent']
                    # add pytest session level vars from config
                    for vname in env_spec.get('vars', []):
                        res[vname] = request.config.getoption(vname)
                else:
                    p_env = env_spec

                if type(p_env) is not str:
                    raise RuntimeError(
                        "{} is not a string: {}"
                        .format(type(p_env), p_env)
                    )

                p_box = request.getfixturevalue(
                    "vagrant_box_{}".format(
                        env_fixture_suffix(os_name, p_env))
                )
                res['parent_source'] = res['parent_box_name'] = p_box.name
                res['skip_add'] = 'true'

            return res

        def _check_box_added(box_name):
            vagrant_rows = h.Vagrant().box("list", parse=True)
            for row in vagrant_rows:
                if (row.data_type == 'box-name') and (row.data[0] == box_name):
                    return True
            return False

        def _add_box(path, name):
            box = h.VagrantBox(name, path=path)
            logger.info(
                "Adding vagrant box '{}'".format(name)
            )
            h.Vagrant().box(
                "add --provider virtualbox --name",
                box.name,
                '--force',
                "'{}'".format(box.path)
            )
            return box

        user_vars = _get_user_vars()

        # TODO separator ???
        box_name = '_'.join([VAGRANT_VMS_PREFIX, base_env, env_level])
        box_path = (
            project_path / '.boxes' / base_env / env_level / 'package.box'
        )

        # TODO for now always rebuild the base box if box file is missed
        #  until smarter logic of boxes rebuild is implemented,
        #  should be triggered when any of the following is true:
        #  - parent env is changed
        #  - input user variables set is changed
        #  - provisioning scripts and other related sources are changed
        if _check_box_added(box_name) and False:
            logger.info(
                "Vagrant box for env '{}:{}' already added"
                .format(base_env, env_level)
            )
            # TODO ??? do not specify package.box here since we don't
            # know whether it exists or not and how it is really related
            # to the box
            return h.VagrantBox(box_name)

        if not box_path.exists():
            pf_name = "packer.{}.json".format(env_level)
            packerfile = project_path / 'images' / 'vagrant' / pf_name
            packer = h.Packer(packerfile)

            logger.info(
                "Building vagrant env '{}' for base env '{}'"
                .format(env_level, base_env)
            )
            # TODO pytest options to turn on packer debug
            packer.build(
                '--force {}'.format(
                    ' '.join([
                        '-var {}={}'.format(k, v) for k, v in user_vars.items()
                    ])
                )
            )

        if not box_path.exists():
            raise RuntimeError(
                "Vagrant box file {} hasn't been created".format(box_path)
            )

        return _add_box(box_path, box_name)

    fixture_builder(
        'session',
        suffix=('_' + env_fixture_suffix(os_name, env_level)),
        module_name=__name__,
        name_with_scope=False
    )(vagrant_box)


for _os_name in BASE_OS_NAMES:
    for _env_level in ENV_LEVELS_HIERARCHY:
        build_vagrant_box_fixture(_os_name, _env_level)

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
        suffix=('_' + env_fixture_suffix(os_name, env_level)),
        module_name=__name__,
        name_with_scope=False
    )(vagrant_machine_shared)


for _os_name in BASE_OS_NAMES:
    for _env_level in ENV_LEVELS_HIERARCHY:
        build_vagrant_machine_shared_fixture(_os_name, _env_level)


@fixture_builder(['module', 'function'], module_name=__name__)
def vagrant_machine_shared(request, env_level, project_path):
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_level')
        if marker:
            env_level = marker.args[0]

    _parts = env_level.split('-')
    os_name = _parts[0]
    env_level = '-'.join(_parts[1:])

    return request.getfixturevalue(
        "vagrant_machine_shared_{}"
        .format(env_fixture_suffix(os_name, env_level))
    )
'''


@pytest.fixture(scope='module')
def post_host_run_hook():
    def f(mhost):
        pass
    return f


@pytest.fixture(scope='module')
def vagrantfile_tmpl():
    return MODULE_DIR / 'Vagrantfile.tmpl'


def docker_container(request, docker_client, base_env, env_level, hosts_spec):
    # TODO API to reuse by other providers
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_level')
        if marker:
            env_level = marker.args[0]

    label = request.fixturename[
        len('docker_container_{}'.format(request.scope)):
    ]

    try:
        hostname = hosts_spec[label]['remote']['hostname']
    except KeyError:
        hostname = None

    try:
        remote_opts = hosts_spec[label]['remote']['specific']['docker']
    except KeyError:
        remote_opts = {}

    with build_remote(
        'docker', request, base_env, env_level, label=label,
        hostname=hostname, specific=remote_opts
    ) as remote:
        yield remote


def vagrant_machine(
    request, base_env, env_level, vagrantfile_tmpl, hosts_spec
):
    # TODO API to reuse by other providers
    if request.scope == 'function':
        marker = request.node.get_closest_marker('env_level')
        if marker:
            env_level = marker.args[0]

        marker = request.node.get_closest_marker('vagrantfile_tmpl')
        if marker:
            vagrantfile_tmpl = marker.args[0]

    label = request.fixturename[
        len('vagrant_machine_{}'.format(request.scope)):
    ]

    try:
        hostname = hosts_spec[label]['remote']['hostname']
    except KeyError:
        hostname = None

    try:
        remote_opts = hosts_spec[label]['remote']['specific']['vbox']
    except KeyError:
        remote_opts = {}

    # TODO configurable way for that
    shared = False
    if shared:
        machine = request.getfixturevalue(
            "vagrant_machine_shared_{}".format(request.scope)
        )
        try:
            # TODO hardcoded
            machine.cmd(
                'snapshot', 'restore', machine.name, 'initial --no-provision'
            )
            yield machine
        finally:
            machine.cmd('halt', '--force')
    else:
        with build_remote(
            'vbox', request, base_env, env_level, label=label,
            vagrantfile_tmpl=vagrantfile_tmpl,
            hostname=hostname, specific=remote_opts
        ) as remote:
            yield remote
            logger.info(
                "Destroying remote '{}'".format(remote.name)
            )


@pytest.fixture(scope='session')
def tmpdir_session(request, tmp_path_factory):
    return tmp_path_factory.getbasetemp()


@pytest.fixture(scope='module')
def tmpdir_module(request, tmp_path_factory):
    return tmp_path_factory.mktemp(safe_filename(request.node.nodeid))


@pytest.fixture
def safe_function_name(request):
    return Path(safe_filename(request.node.name))


@pytest.fixture
def tmpdir_function(safe_function_name, tmpdir_module):
    res = tmpdir_module / safe_function_name
    res.mkdir()
    return res


@pytest.fixture
def ssh_config(request, tmpdir_function):
    return tmpdir_function / "ssh_config"


@pytest.fixture
def hosts(request):
    hosts = ['']
    marker = request.node.get_closest_marker('hosts')
    if marker:
        hosts = marker.args[0]

    return hosts


@pytest.fixture
def hosts_meta():
    return {}


@pytest.fixture
def mock_hosts(hosts, request, mlocalhost):
    mocked = defaultdict(list)

    marker = request.node.get_closest_marker('mock_cmds')
    if not marker:
        return

    try:
        for label, cmds in marker.args[0].items():
            if label in hosts:
                fixture_name = 'mhost' + label
                mhost = request.getfixturevalue(fixture_name)
                assert mhost is not mlocalhost  # TODO more clever check
                for cmd in cmds:
                    if type(cmd) is dict:
                        cmd, cmd_mock = next(iter(cmd.items()))
                    else:
                        cmd_mock = None
                    mock_system_cmd(mhost.host, cmd, cmd_mock=cmd_mock)
                    mocked[fixture_name].append(cmd)
        yield
    finally:
        for fixture_name, cmds in mocked.items():
            mhost = request.getfixturevalue(fixture_name)
            for cmd in cmds:
                restore_system_cmd(mhost.host, cmd)


@pytest.fixture
def inject_ssh_config(hosts, mlocalhost, ssh_config, ssh_key, request):
    target_hosts = set(hosts)
    ssh_config_paths = {}
    def_ssh_config = '~/.ssh/config'

    marker = request.node.get_closest_marker('inject_ssh_config')
    if marker:
        target_hosts = set(marker.args[0]) & set(hosts)

    for label in target_hosts:
        mhost = request.getfixturevalue('mhost' + label)
        assert mhost is not mlocalhost
        for path in (ssh_config, ssh_key):
            mhost.check_output("mkdir -p {}".format(path.parent))
            mlocalhost.check_output(
                "scp -p -F {} {} {}:{}".format(
                    ssh_config, path, mhost.hostname, path
                )
            )
        mhost.check_output("mkdir -p ~/.ssh")
        mhost.check_output('cp -p {} {}'.format(ssh_config, def_ssh_config))
        ssh_config_paths[label] = Path(
            mhost.check_output('realpath {}'.format(def_ssh_config))
        )
    return ssh_config_paths


@pytest.fixture
def cortx_spec(request):
    marker = request.node.get_closest_marker('cortx_spec')
    spec = marker.args[0] if marker else DEFAULT_CLUSTER_SPEC
    return spec


# cortx_spec sanity checks
@pytest.fixture
def _cortx_spec(cortx_spec):
    assert (
        len(
            {
                k: v for k, v in cortx_spec.items()
                if "primary" in v['roles']
            }
        ) == 1
    )
    return cortx_spec


@pytest.fixture
def cortx_hosts(hosts, _cortx_spec, request):
    _hosts = defaultdict(dict)
    for label in hosts:
        if label in _cortx_spec:
            _hosts[label]['minion_id'] = _cortx_spec[label]['minion_id']
            _hosts[label]['roles'] = _cortx_spec[label].get(
                'roles', True
            )

    return _hosts


@pytest.fixture
def cortx_primary_host_label(cortx_hosts):
    return [k for k, v in cortx_hosts.items() if "primary" in v['roles']][0]


@pytest.fixture
def cortx_primary_mhost(cortx_primary_host_label, request):
    return request.getfixturevalue('mhost' + cortx_primary_host_label)


@pytest.fixture
def cortx_primary_host_ip(cortx_primary_mhost):
    return cortx_primary_mhost.host.interface(
        cortx_primary_mhost.interface
    ).addresses[0]


@pytest.fixture
def install_provisioner(
    cortx_hosts, mlocalhost, project_path, ssh_config, request
):
    assert cortx_hosts, "the fixture makes sense only for Cortx hosts"

    for label in cortx_hosts:
        mhost = request.getfixturevalue('mhost' + label)
        mlocalhost.check_output(
            "bash -c \". {script_path} "
            "&& install_provisioner {repo_src} {prvsnr_version} {hostspec} "
            "{ssh_config} {sudo} {singlenode}\""
            .format(
                script_path=(
                    project_path / 'cli/src/common_utils/functions.sh'
                ),
                repo_src='local',
                prvsnr_version="''",
                hostspec=mhost.hostname,
                ssh_config=ssh_config,
                sudo='false',
                singlenode=('true' if len(cortx_hosts) == 1 else 'false')
            )
        )


@pytest.fixture
def configure_salt(
    cortx_hosts, install_provisioner, cortx_primary_host_ip, request
):
    cli_dir = PRVSNR_REPO_INSTALL_DIR / 'cli' / 'src'

    for label, host_spec in cortx_hosts.items():
        minion_id = host_spec['minion_id']
        is_primary = (
            'true' if "primary" in host_spec['roles'] else 'false'
        )
        primary_host = (
            "localhost" if "primary" in host_spec['roles']
            else cortx_primary_host_ip
        )
        mhost = request.getfixturevalue('mhost' + label)
        mhost.check_output(
            ". {} && configure_salt '{}' '' '' '' {} {}".format(
                cli_dir / 'common_utils/functions.sh',
                minion_id,
                is_primary,
                primary_host
            )
        )


@pytest.fixture
def accept_salt_keys(cortx_hosts, install_provisioner, cortx_primary_mhost):
    cli_dir = PRVSNR_REPO_INSTALL_DIR / 'cli' / 'src'

    for label, host_spec in cortx_hosts.items():
        cortx_primary_mhost.check_output(". {} && accept_salt_key '{}'".format(
            cli_dir / 'common_utils/functions.sh', host_spec['minion_id'])
        )

    cortx_primary_mhost.check_output("salt '*' mine.update")


@pytest.fixture
def sync_salt_modules(cortx_primary_mhost, install_provisioner):
    cortx_primary_mhost.check_output("salt '*' saltutil.sync_modules")
    cortx_primary_mhost.check_output("salt-run saltutil.sync_modules")


@pytest.fixture
def mlocalhost(localhost, request):
    return LocalHostMeta(
        None, localhost, None, request, label=None, interface='lo'
    )


@pytest.fixture
def vagrant_default_ssh(request, hosts):
    res = (len(hosts) < 2)
    marker = request.node.get_closest_marker('vagrant_default_ssh')
    if marker:
        res = marker.args[0]
    return res


def build_remote(
    env_provider, request, os_name, env_level,
    label=None, base_level=None, **kwargs
):
    base_name = h.remote_name(
        request.node.nodeid, request.scope, os_name, env_level, label=label
    )

    if base_level is None:
        logger.info(
            "Building env-level '{}' for os '{}' with provider '{}'"
            .format(env_level, os_name, env_provider)
        )
        # TODO return an object of a class
        if env_provider == 'docker':
            base_level = request.getfixturevalue(
                "docker_image_{}".format(
                    env_fixture_suffix(os_name, env_level)
                )
            )
        elif env_provider == 'vbox':
            base_level = request.getfixturevalue(
                "vagrant_box_{}".format(env_fixture_suffix(os_name, env_level))
            )
        else:
            raise ValueError("unknown env provider {}".format(env_provider))

    tmpdir = request.getfixturevalue('tmpdir_' + request.scope)

    logger.info(
        "Starting remote with base name '{}'".format(base_name)
    )
    remote = h.run_remote(
        env_provider, base_level, base_name, tmpdir, **kwargs
    )
    logger.info(
        "Started remote '{}'".format(remote.name)
    )
    return remote


def discover_remote(
    request, remote, ssh_config=None, host_fixture_label=None
):
    tmpdir = request.getfixturevalue('tmpdir_{}'.format(request.scope))
    local_user_id = request.getfixturevalue('local_user_id')
    local_user_name = request.getfixturevalue('local_user_name')

    _host = None
    # TODO add support for local user host for non-docker cases
    _host_user = None
    _iface = 'eth0'
    _ssh_config = None
    if isinstance(remote, h.Container):
        # update container data
        remote.container.reload()
        _host = testinfra.get_host(remote.container.id, connection='docker')
        if int(local_user_id) == 0:
            _host_user = _host
        else:
            _host.check_output(
                f"adduser -u {local_user_id}"
                f" {local_user_name}"
            )
            _host_user = testinfra.get_host(
                f"{local_user_name}@{remote.container.id}",
                connection='docker'
            )

        #  ssh to be up
        service = _host.service
        #   TODO service name is 'ssh' on debian, ubuntu, ... ???
        service_name = 'sshd'
        while not service(service_name).is_running:
            time.sleep(.5)
        # TODO verify that eth0 is always true for docker
    elif isinstance(remote, h.VagrantMachine):
        # in vagrant ssh-config a machine is accessible
        # via localhost:localport, use that as a temporary
        # way to get its own ip and access its internal ssh port
        _ssh_config_tmp = tmpdir / "ssh_config.{}.tmp".format(remote.name)
        with _ssh_config_tmp.open('w') as f:
            f.write(remote.ssh_config())

        # FIXME sometimes hostonlynetwork of a vbox machine is not up properly
        # (route table is not created), no remedy found yet,
        # possible workaround is to remove vbox hostonly network for
        # the machine and re-create the machine
        # https://jts.seagate.com/browse/EOS-3129

        # vagrant uses vagrant machine name as Host ID in ssh-config
        _host = testinfra.get_host(
            "ssh://{}".format(remote.name), ssh_config=str(_ssh_config_tmp)
        )
        _iface = 'enp0s8'
        if request.getfixturevalue('vagrant_default_ssh'):
            _ssh_config = remote.ssh_config().replace(
                remote.name, remote.hostname
            )

    else:
        raise ValueError(
            "unexpected remote type: {}".format(type(remote))
        )

    # TODO there might be some cheaper way
    #      (e.g. get from testinfra host object)
    _hostname = _host.check_output('hostname')

    if ssh_config is None:
        ssh_config = tmpdir / 'ssh_config.{}'.format(remote.name)
    ssh_config.touch(mode=0o600, exist_ok=True)

    # prepare ssh configuration
    if _ssh_config is None:
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

    return HostMeta(
        remote,
        _host,
        ssh_config,
        request,
        label=host_fixture_label,
        machine_name=remote.name,
        interface=_iface,
        host_user=_host_user
    )


def build_mhost_fixture(label=None, module_name=__name__):
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

    def host(request):
        label = request.fixturename[len('host'):]
        _mhost_fixture_name = 'mhost' + label
        # ensure that related host fixture has been actually called
        mhost = request.getfixturevalue(_mhost_fixture_name)
        return mhost.host

    fixture_builder(
        'function',
        suffix=label,
        module_name=module_name,
        name_with_scope=False
    )(host)

    @fixture_builder(
        "function", suffix=label, module_name=module_name,
        name_with_scope=False
    )
    def mhost(localhost, request, tmpdir_function, hosts_meta, env_provider):
        if env_provider == 'host':
            return request.getfixturevalue('mlocalhost')

        scope = (
            'function' if request.node.get_closest_marker('isolated')
            else 'module'
        )

        ssh_config = request.getfixturevalue('ssh_config')

        logger.info(
            "Building remote '{}' using provider '{}'"
            .format('default' if label is None else label, env_provider)
        )

        if env_provider == 'docker':
            remote = request.getfixturevalue(
                remote_fixtures[scope]['docker'].__name__
            )
        else:
            # TODO skip if vagrant or packer or virtualbox is not installed
            # pytest.skip()
            remote = request.getfixturevalue(
                remote_fixtures[scope]['vagrant'].__name__
            )

        logger.info(
            "Discovering remote '{}'".format(remote.name)
        )
        meta = discover_remote(
            request, remote,
            ssh_config=ssh_config, host_fixture_label=label
        )

        hosts_meta[meta.fixture_name] = meta

        # TODO add try-catch and remove default implementation
        #      of post_host_run_hook
        request.getfixturevalue('post_host_run_hook')(meta)

        return meta


# default 'host' fixture is always present
build_mhost_fixture()
# also host fixtures for CORTX stack makes sense
for node_id in range(1, MAX_NODES_NUMBER + 1):
    build_mhost_fixture(f'srvnode{node_id}')
