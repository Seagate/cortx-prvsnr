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

from enum import Enum
import sys
import os
import re
import csv
from pathlib import Path
import docker
import testinfra
from abc import ABC, abstractmethod
from random import randrange
from time import sleep
import logging

import pytest

from provisioner.vendor import attr

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent

PROVISIONER_API_DIR = (MODULE_DIR.parent / 'api/python').resolve()
sys.path.insert(0, str(PROVISIONER_API_DIR))
from provisioner.config import *  # noqa: E402, F403, F401 TODO improve

# just to make flake8 happy
from provisioner.config import PRVSNR_ROOT_DIR, PROJECT_PATH  # noqa: E402

PRVSNR_REPO_INSTALL_DIR = PRVSNR_ROOT_DIR

PRVSNR_PKG_NAME = 'cortx-prvsnr'
PRVSNR_API_PKG_NAME = 'python36-cortx-prvsnr'
PRVSNR_CLI_PKG_NAME = 'cortx-prvsnr-cli'
# TODO verification is required (docker containers, virtualbox machines, ...)
MAX_REMOTE_NAME_LEN = 80

localhost = testinfra.get_host('local://')

BUILD_BUNDLE_SCRIPT = (
    (PROJECT_PATH or PRVSNR_ROOT_DIR)
    / 'srv/misc_pkgs/mocks/cortx/files/scripts/buildbundle.sh'
)

if not BUILD_BUNDLE_SCRIPT.exists():
    BUILD_BUNDLE_SCRIPT = None


class BundleT(Enum):

    """Bundle types."""

    DEPLOY_CORTX = 'deploy-cortx'
    DEPLOY_BUNDLE = 'deploy-bundle'
    UPGRADE = 'upgrade'


class LevelT(Enum):

    """Test level types."""

    NOLEVEL = 'nolevel'
    UNIT = 'unit'
    INTEGRATION_MOCKED = 'integration_mocked'
    INTEGRATION = 'integration'
    SYSTEM = 'system'


class TopicT(Enum):

    """Test topic types."""

    NOTOPIC = 'notopic'
    DEPLOY = 'deploy'
    CONFIG = 'config'
    UPGRADE_BUNDLE = 'upgrade_bundle'
    UPGRADE = 'upgrade'


# TODO check packer is available
@attr.s
class Packer:
    packerfile = attr.ib(
        converter=lambda v: v.resolve()
    )
    log = attr.ib(default=True)
    err_to_out = attr.ib(default=True)
    _localhost = attr.ib(
        init=False, default=localhost
    )

    @packerfile.validator
    def _check_packerfile(self, attribute, value):
        if not value.is_file:
            raise ValueError(
                "{} is not a file".format(value)
            )
        self.validate()

    def check_output(self, cmd, err_to_out=None):
        res = None
        err_to_out = (self.err_to_out if err_to_out is None else err_to_out)
        try:
            res = self._localhost.run(
                cmd + (' 2>&1' if err_to_out else '')
            )
            assert res.rc == 0
        finally:
            if res is not None:
                for line in res.stderr.split(os.linesep):
                    logger.debug(line)
                for line in res.stdout.split(os.linesep):
                    logger.debug(line)
        return res.stdout

    def packer(self, command, *args, **kwargs):
        return self.check_output(
            "{}packer {} {} '{}'".format(
                "PACKER_LOG=1 " if self.log else '',
                command,
                ' '.join([*args]), self.packerfile
            ), **kwargs
        )

    # TODO use some dynamic way instead
    def build(self, *args):
        return self.packer("build", *args)

    def validate(self, *args):
        return self.packer("validate", *args)


# TODO with manager
class Remote(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def destroy(self, ok_if_missed=True, force=True):
        pass

    # TODO force=False doesn't have any sense for automated scope
    @staticmethod
    @abstractmethod
    def destroy_by_name(remote_name, ok_if_missed=True, force=True):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.destroy()


@attr.s
class Container(Remote):
    name = attr.ib()
    image = attr.ib()
    hostname = attr.ib(default=None)
    container = attr.ib(init=False, default=None)
    specific = attr.ib(default=attr.Factory(dict))
    volumes = attr.ib(
        init=False,
        default=attr.Factory(lambda: {
            '/sys/fs/cgroup': {'bind': '/sys/fs/cgroup', 'mode': 'ro'}
        })
    )

    client = docker.from_env()

    def __attrs_post_init__(self):
        if self.hostname is None:
            self.hostname = safe_hostname(self.name)

        self.volumes.update(self.specific.pop('volumes', {}))

    def run(self):
        if self.container is not None:
            raise RuntimeError("already running")  # some API error

        try:
            self.container = self.client.containers.run(
                self.image,
                name=self.name,
                # it's safer to not exceed 64 chars on Unix systems
                # for the hostname
                # (real limit might be get using `getconf HOST_NAME_MAX`)
                hostname=self.hostname,
                detach=True,
                tty=True,
                # network=network_name,
                volumes=self.volumes,
                # security_opt=['seccomp=unconfined'],
                tmpfs={'/run': '', '/run/lock': ''},
                ports={'22/tcp': None},
                **self.specific
            )
        except Exception as exc:
            self.destroy()
            if isinstance(exc, docker.errors.APIError):
                if 'is already in use' in str(exc):
                    # TODO ? try to remove is it's not running
                    raise RemoteAlreadyInUse(self.name)
            raise

    def destroy(self, ok_if_missed=True, force=True):
        self.container = None
        self.destroy_by_name(self.name, ok_if_missed=ok_if_missed, force=force)

    @staticmethod
    def destroy_by_name(container_name, ok_if_missed=True, force=True):
        try:
            container = Container.client.containers.get(container_name)
        except Exception:  # TODO less generic exception
            # container with the name might not be even created yet
            if ok_if_missed:
                logger.info(
                    'Container with name {} is missed'.format(container_name)
                )
            else:
                raise
        else:
            container.remove(force=force)


@attr.s
class VagrantError(Exception):
    rc = attr.ib()
    stdout = attr.ib()
    stderr = attr.ib()


class VagrantAlreadyInUseError(VagrantError):
    pass


class RemoteError(Exception):
    pass


@attr.s
class RemoteNotExist(RemoteError):
    name = attr.ib()


@attr.s
class RemoteAlreadyInUse(RemoteError):
    name = attr.ib()


# TODO seems the format is not yet finallized by vagrant
#      (https://www.vagrantup.com/docs/cli/machine-readable.html)
@attr.s
class VagrantParsedRow:
    _row = attr.ib()  # should be a csv row for now
    ts = attr.ib(init=False, default=None)
    target = attr.ib(init=False, default=None)
    data_type = attr.ib(init=False, default=None)
    data = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        row = next(csv.reader([self._row]))
        self.ts, self.target, self.data_type = row[:3]
        self.data = row[3:]


# TODO check packer is available
@attr.s
class Vagrant:
    # TODO validate
    env_vars = attr.ib(default=None)
    log = attr.ib(default='error')
    err_to_out = attr.ib(default=True)
    _env_prefix = attr.ib(default='')
    _localhost = attr.ib(
        init=False,
        default=localhost
    )

    def __attrs_post_init__(self):
        if self.env_vars is not None:
            self._env_prefix = ' '.join(
                ["{}='{}'".format(n, v) for (n, v) in self.env_vars]
            ) + ' '

    def check_output(self, cmd, err_to_out=None):
        res = None
        err_to_out = (self.err_to_out if err_to_out is None else err_to_out)
        try:
            res = self._localhost.run(
                self._env_prefix + cmd + (' 2>&1' if err_to_out else '')
            )
            if res.rc != 0:
                raise VagrantError(res.rc, res.stdout, res.stderr)

        finally:
            if res is not None:
                for line in res.stderr.split(os.linesep):
                    logger.debug(line)
                for line in res.stdout.split(os.linesep):
                    logger.debug(line)
        return res.stdout

    def vagrant(self, command, *args, parse=False, **kwargs):
        if parse:
            kwargs['err_to_out'] = False

        output = self.check_output(
            "{}vagrant {} {} {}".format(
                "VAGRANT_LOG={} ".format(self.log) if self.log else '',
                '--machine-readable' if parse else '',
                command,
                ' '.join([*args])
            ), **kwargs
        )
        if parse:
            return [
                VagrantParsedRow(row)
                for row in output.split(os.linesep) if row
            ]
        else:
            return output

    # TODO use some dynamic way instead
    def ssh(self, *args, **kwargs):
        return self.vagrant("ssh --", *args, **kwargs)

    def ssh_config(self, *args, **kwargs):
        return self.vagrant("ssh-config", *args, err_to_out=False, **kwargs)

    def validate(self, *args, **kwargs):
        return self.vagrant("validate", *args, **kwargs)

    def up(self, *args, **kwargs):
        try:
            self.vagrant("up", *args, **kwargs)
        except VagrantError as exc:
            if (('already exists' in exc.stderr) or
                    ('Machine already provisioned' in exc.stdout)):
                raise VagrantAlreadyInUseError(exc.rc, exc.stderr, exc.stdout)
            else:
                raise

    def destroy(self, *args, **kwargs):
        return self.vagrant("destroy", *args, **kwargs)

    def box(self, *args, **kwargs):
        return self.vagrant("box", *args, **kwargs)

    def cmd(self, cmd, *args, **kwargs):
        return self.vagrant(cmd, *args, **kwargs)


# TODO check vagrant is available
@attr.s
class VagrantMachine(Remote):

    VAGRANTFILE_TMPL = MODULE_DIR / 'Vagrantfile.tmpl'

    # TODO validators for all
    name = attr.ib()
    vm_dir = attr.ib(default=None)
    vagrantfile = attr.ib(default=None)
    provider = attr.ib(default='vbox')
    user_vars = attr.ib(default={})

    # TODO should be required if default template is used
    box = attr.ib(default=None)
    # Path or string
    vagrantfile_tmpl = attr.ib(
        converter=lambda v: v.read_text() if isinstance(v, Path) else v,
        default=VAGRANTFILE_TMPL.read_text()
    )
    hostname = attr.ib(
        converter=lambda v: None if v is None else safe_hostname(v),
        default=None
    )
    memory = attr.ib(
        converter=lambda v: int(v), default=1024
    )
    cpus = attr.ib(
        converter=lambda v: int(v), default=1
    )
    specific = attr.ib(default={})
    log = attr.ib(default='error')

    last_status = attr.ib(init=False, default=None)
    # TODO factory to set {} as default
    _vagrant = attr.ib(init=False, default=None)
    _localhost = attr.ib(init=False, default=testinfra.get_host('local://'))

    def __attrs_post_init__(self):
        if self.hostname is None:
            self.hostname = safe_hostname(self.name)

        if self.vagrantfile is None:
            assert self.vm_dir

            if not self.vm_dir.exists():
                self.vm_dir.mkdir()

            if 'cpus' not in self.specific:
                self.specific['cpus'] = self.cpus

            if 'memory' not in self.specific:
                self.specific['memory'] = self.memory

            self.vagrantfile = self.vm_dir / 'Vagrantfile'
            self.vagrantfile.write_text(
                self.vagrantfile_tmpl.format(
                    box_name=self.box.name,
                    vm_name=self.name,
                    hostname=self.hostname,
                    vm_dir=self.vm_dir,
                    **self.specific
                )
            )

        self._vagrant = Vagrant(
            log=self.log, env_vars=[
                ('VAGRANT_CWD', self.vagrantfile.parent),
                ('VAGRANT_VAGRANTFILE', self.vagrantfile.name)
            ] + [(k, v) for k, v in self.user_vars.items()]
        )
        self.last_status = {}

        self.validate()

    # TODO use some dynamic way instead
    def ssh(self, *args):
        return self._vagrant.ssh(*args)

    def ssh_config(self, *args):
        return self._vagrant.ssh_config(*args)

    def validate(self, *args):
        return self._vagrant.validate(*args)

    def up(self, *args, prune=True):
        if prune:
            # ensure that no orphan VirtualBox machine is running
            status = self.status(update=False)
            if status['state'][0] == 'not_created':
                # TODO that is stuck to VBox only
                self._localhost.run(
                    'VBoxManage unregistervm --delete {}'.format(self.name)
                )

        return self._vagrant.up(*args)

    def run(self):
        try:
            self.up()
        except Exception as exc:
            self.destroy(ok_if_missed=True, force=True)
            if isinstance(exc, VagrantAlreadyInUseError):
                raise RemoteAlreadyInUse(self.name)
            raise

    def destroy(self, ok_if_missed=True, force=True):
        _args = ['--force'] if force else []
        try:
            self._vagrant.destroy(*_args)
        except VagrantError as exc:
            # TODO custom error for that case
            if (
                "machine with the name '{}' was not found configured"
                .format(self.name) in exc.stderr
            ):
                if ok_if_missed:
                    logger.info(
                        'Vagrant machine with name {} is missed'
                        .format(self.name)
                    )
                    return
                else:
                    raise RemoteNotExist(self.name)
            raise

    @staticmethod
    def destroy_by_name(machine_name, ok_if_missed=True, force=True):
        # TODO move to module level, a kind of singletone
        global_status = run(
            localhost,
            'vagrant global-status --prune | grep {}'.format(machine_name)
        )
        if global_status.rc != 0:  # missed
            if ok_if_missed:
                return
            else:
                raise RemoteNotExist(
                    'Vagrant machine with name {} is missed'
                    .format(machine_name)
                )

        machine_id = global_status.stdout.split()[0]
        _args = ['--force'] if force else []
        Vagrant().destroy(*_args, machine_id)

    def cmd(self, cmd, *args):
        return self._vagrant.cmd(cmd, *args)

    def status(self, *args, update=False):
        if not self.last_status or update:
            raw_status = self._vagrant.cmd('status', *args, parse=True)
            self.last_status.clear()
            for row in raw_status:
                # TODO possible other cases: empty target and 'ui' as type
                if row.target == self.name:
                    self.last_status[row.data_type] = row.data

        return self.last_status


@attr.s
class VagrantBox:
    name = attr.ib()
    path = attr.ib(
        converter=lambda v: v.resolve() if v else None,
        default=None
    )

    @path.validator
    def _check_path(self, attribute, value):
        if value and (not value.is_file):
            raise ValueError(
                "{} is not a file".format(value)
            )


# just some common sense for now
def safe_filename(name):
    re_filename = re.compile(r'([^a-zA-Z0-9_.-])')
    return re_filename.sub(r'_', name)


def sanitize_remote_name_part(name):
    re_remote_non_sanitized = re.compile(r'([^a-zA-Z0-9])')
    return re_remote_non_sanitized.sub(r'', name)


# TODO
# - tests
# - check chars at the beginning and end
def safe_remote_name(name):
    re_unsafe_remote_chars = re.compile(r'([^a-zA-Z0-9_.-])')
    return re_unsafe_remote_chars.sub(r'_', name)[-MAX_REMOTE_NAME_LEN:]


def remote_name(test_node_id, scope, osname, env_level, label=None):
    parts = [
        sanitize_remote_name_part(i) for i in [
            test_node_id, scope, osname, env_level, label
        ] if i
    ]
    return safe_remote_name('_'.join(parts))


# TODO
# - tests
# - check chars at the beginning and end
def safe_docker_container_name(name):
    re_container_name = re.compile(r'([^a-zA-Z0-9_.-])')
    return re_container_name.sub(r'_', name)[-MAX_REMOTE_NAME_LEN:]


# TODO
# - reasearch real limitations
# - test
def safe_vagrant_machine_name(name):
    return safe_docker_container_name(name)


# TODO
# - tests
# - better satisfy RFC 1123 (https://tools.ietf.org/html/rfc1123#page-13)
# - ??? actually docker used to check hostnames but is not clear
#   how it happens now
#   (
#       https://github.com/moby/moby/issues/20371,
#       https://github.com/moby/moby/pull/20566
#   )
def safe_hostname(name):
    re_hostname = re.compile(r'([^a-zA-Z0-9-])')
    re_multiple_dahses = re.compile(r'-+')
    _s = re_hostname.sub('-', name)
    return re_multiple_dahses.sub('-', _s).lower()[-63:].lstrip('-')


def mock_system_cmd(host, cmd, cmd_mock=None, bin_path='/usr/local/bin'):
    # TODO might not work in some cases
    cmd_orig = host.run('which {}'.format(cmd))
    if cmd_orig.rc == 0:
        cmd_orig = cmd_orig.stdout.strip()
        host.check_output('mv -f {0} {0}.bak'.format(cmd_orig))

    # TODO shell quotes interpreting might impact expected output
    if cmd_mock is None:
        cmd_mock = 'echo {}-ARGS: "$@"'.format(cmd.upper())

    cmd_mock = '#!/bin/bash\n{}'.format(cmd_mock)
    cmd_path = Path(bin_path) / cmd
    host.check_output("echo -e '{}'>{}".format(cmd_mock, cmd_path))
    host.check_output("chmod +x {}".format(cmd_path))


def restore_system_cmd(host, cmd, bin_path='/usr/local/bin'):
    cmd_path = Path(bin_path) / cmd
    host.check_output('rm -f {}'.format(cmd_path))

    cmd_orig = host.run('which {}.bak'.format(cmd))
    if cmd_orig.rc == 0:
        cmd_orig = cmd_orig.stdout.strip()
        host.check_output('mv -f {} {}'.format(cmd_orig, cmd_orig[:-4]))


def fixture_builder(
    scope, name_with_scope=True, suffix=None,
    module_name=__name__, fixture_name=None
):

    scopes = scope if type(scope) in (list, tuple) else [scope]

    def _builder(f):
        res = []
        mod = sys.modules[module_name]

        for _scope in scopes:
            name_parts = [
                part for part in (
                    f.__name__,
                    ('_' + _scope) if name_with_scope else None,
                    suffix
                ) if part
            ] if fixture_name is None else [fixture_name]
            _f = pytest.fixture(scope=_scope)(f)
            setattr(_f, '__name__', ''.join(name_parts))
            setattr(mod, _f.__name__, _f)
            res.append(_f)
        return res if scopes is scope else res[0]

    return _builder


def _docker_image_build(client, dockerfile, ctx, image_name=None):
    # build image from the Dockerfile
    output = []
    kwargs = {}
    if image_name:
        kwargs['tag'] = image_name
    try:
        image, output = client.images.build(
            dockerfile=str(dockerfile), path=str(ctx), **kwargs
        )
    except Exception as exc:
        print("Failed to build docker image: {}".format(exc))
        raise
    finally:
        logger.debug(
            "Docker build logs ...\n:"
            "=====================\n"
        )
        for line in output:
            logger.debug(line)
    return image


def _docker_container_commit(container, repository=None, tag=None):
    # commit an image from the running container
    try:
        return container.container.commit(repository=repository, tag=tag)
    except Exception as exc:
        print("Failed to commit docker image: {}".format(exc))
        raise


def run_remote(provider, base_level, base_name, tmpdir, *args, **kwargs):
    base_name = base_name[-(MAX_REMOTE_NAME_LEN-3):]

    for i in range(3):  # just three tries
        _id = randrange(100)
        name = '{}_{:02d}'.format(base_name, _id)

        if provider == 'docker':
            remote = Container(name, base_level, *args, **kwargs)
        elif provider == 'vbox':
            vm_dir = tmpdir / safe_filename(name)
            remote = VagrantMachine(
                name, vm_dir=vm_dir,
                box=base_level,
                *args, **kwargs
            )
        else:
            raise RuntimeError('unknown provider')

        try:
            remote.run()
        except RemoteAlreadyInUse:
            logger.warning(
                'remote {} with name {} is already in use'
                .format(Container, name)
            )
        else:
            return remote
    else:
        raise RuntimeError(
            "unexpected number of remotes with base name {} are already in use"
            .format(base_name)
        )


# TODO use object proxy for testinfra's host instances instead
def run(host, script, *args, quiet=False, force_dump=False, **kwargs):
    res = None
    try:
        res = host.run(script, *args, **kwargs)
    finally:
        # TODO it takes very much time if stdout/stderr are very long
        # (e.g. minutes for salt logs)
        if (res is not None) and ((res.rc != 0 and not quiet) or force_dump):
            if res.stdout:
                for line in res.stdout.strip().split(os.linesep):
                    logger.info(line)
            if res.stderr:
                for line in res.stderr.strip().split(os.linesep):
                    logger.error(line)
    return res


def check_output(host, script, *args, **kwargs):
    res = run(host, script, *args, **kwargs)
    assert res.rc == 0
    return res.stdout.rstrip("\r\n")


def inject_repo(host, ssh_config, local_repo_tgz, host_repo_dir=None):
    host_repo_tgz = Path('/tmp') / local_repo_tgz.name

    if host_repo_dir is None:
        host_repo_dir = Path('/tmp') / PROJECT_PATH.name

    hostname = host.check_output('hostname')
    localhost.check_output(
        'scp -F "{}" "{}" {}:"{}"'.format(
            ssh_config,
            local_repo_tgz,
            hostname,
            host_repo_tgz
        )
    )
    host.check_output(
        'mkdir -p "{0}" && tar -zxf "{1}" -C "{0}"'
        .format(host_repo_dir, host_repo_tgz)
    )
    return host_repo_dir


def collect_ip4_addrs(host):
    res = []

    ifaces = host.check_output(
        "ip link show up | grep -v -i loopback "
        "| sed -n 's/^[0-9]\\+: \\([^:@]\\+\\).*/\\1/p'"
    )

    for interface in ifaces.strip().split(os.linesep):
        for addr in host.interface(interface).addresses:
            # Note. will include ip6 as well
            # TODO verify that it will work for all cases
            if not (':' in addr or addr in res):
                res.append(addr)

    return res


def list_dir(path, host=localhost):
    res = host.check_output(
        'bash -c "set -o pipefail; '
        'cd {} && find . -type f -print | LANG=C sort"'
        .format(path)
    )
    return res.split()


# TODO requires md5sum and other system tools
def hash_dir(path, host=localhost):
    res = host.check_output(
        'bash -c "set -o pipefail; '
        'cd {} && find . -type f -print0 | LANG=C sort -z '
        '| xargs -0 md5sum | md5sum"'
        .format(path)
    )
    return res.split()[0]


def hash_file(path, host=localhost):
    res = host.check_output('md5sum {}'.format(path))
    return res.split()[0]


# TODO eventually helper
def ensure_motr_is_online(mhost, num_tries=120):
    # ensure that motr in online
    re_status = re.compile(r' +\[ *(.+)\]')
    for i in range(num_tries):
        motr_status = mhost.check_output("hctl motr status")
        logger.debug('motr status, try {}: {}'.format(i + 1, motr_status))
        for line in motr_status.split('\n'):
            m = re_status.match(line)
            if m and m.group(1) != 'online':
                sleep(1)
                break
        else:
            logger.info(
                'motr becomes online after {} checks:\n{}'
                .format(i + 1, motr_status)
            )
            break
    else:
        assert False, (
            'motr is not online after {} tries, last status: {}'
            .format(num_tries, motr_status)
        )


def bootstrap_cortx(mhost):
    logger.info('Bootstrapping the cluster')
    mhost.check_output(
        'bash {} -vv -S'
        .format(PRVSNR_REPO_INSTALL_DIR / 'cli/bootstrap')
    )
    ensure_motr_is_online(mhost)


def install_provisioner_api(mhost):
    mhost.check_output("pip3 install {}".format(mhost.repo / 'api/python'))


def dump_options(request, run_options):
    opts_str = '\n'.join([
        '{}: {}'.format(opt, request.config.getoption(opt.replace('-', '_')))
        for opt in run_options
    ])
    logger.info('Passed options:\n{}'.format(opts_str))


def add_options(parser, options):
    for name, params in options.items():
        name = (name if name.startswith('--') else f"--{name}")
        parser.addoption(name, **params)
