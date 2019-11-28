import sys
import os
import re
import csv
from copy import deepcopy
from pathlib import Path
import attr
import docker
import testinfra
from abc import ABC, abstractmethod
from random import randrange

import pytest
from functools import wraps

import logging
logger = logging.getLogger(__name__)

PRVSNR_REPO_INSTALL_DIR = Path('/opt/seagate/eos-prvsnr')
# TODO verification is required (docker containers, virtualbox machines, ...)
MAX_REMOTE_NAME_LEN = 80


@attr.s
class HostMeta:
    # TODO validators for all
    remote = attr.ib()
    host = attr.ib()
    ssh_config = attr.ib()
    fixture_name = attr.ib(default=None)
    machine_name = attr.ib(default=None)
    hostname = attr.ib(default=None)
    iface = attr.ib(default=None)

    def __attrs_post_init__(self):
        if self.hostname is None:
            self.hostname = self.host.check_output('hostname')

        # TODO more smarter logic to get iface that is asseccible from host
        # (relates to https://github.com/hashicorp/vagrant/issues/2779)
        if self.iface is None:
            if (
                isinstance(self.remote, VagrantMachine) and
                (self.remote.provider == 'vbox')
            ):
                self.iface = 'eth1'
            else:
                self.iface = 'eth0'

        assert self.host.interface(self.iface).exists


# TODO check packer is available
@attr.s
class Packer:
    packerfile = attr.ib(
        converter=lambda v: v.resolve()
    )
    log = attr.ib(default=True)
    err_to_out = attr.ib(default=True)
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
            "{}packer {} {} {}".format(
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
    def destroy(self, ok_if_missed=True, force=True):
        pass

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
    container = attr.ib()
    name = attr.ib(init=False, default=None)

    client = docker.from_env()

    def __attrs_post_init__(self):
        self.name = self.container.name

    def destroy(self, ok_if_missed=True, force=True):
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


class RemoteError():
    pass


@attr.s
class RemoteNotExist(RemoteError):
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
        default=testinfra.get_host('local://')
    )

    def __attrs_post_init__(self):
        if self.env_vars is not None:
            self._env_prefix = ' '.join(
                ["{}={}".format(n, v) for (n, v) in self.env_vars]
            ) + ' '

    def check_output(self, cmd, err_to_out=None):
        res = None
        err_to_out = (self.err_to_out if err_to_out is None else err_to_out)
        try:
            res = self._localhost.run(
                self._env_prefix + cmd + (' 2>&1' if err_to_out else '')
            )
            if res.rc != 0:
                raise VagrantError(res)

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
            return [VagrantParsedRow(row) for row in output.split(os.linesep) if row]
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
    provider = attr.ib(default='vbox')
    # TODO should be required if default template is used
    box = attr.ib(default=None)
    vagrantfile = attr.ib(
        converter=lambda v: None if v is None else v.resolve(),
        default=None
    )
    vagrantfile_dest = attr.ib(
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
    log = attr.ib(default='error')
    last_status = attr.ib(
        init=False,
        default=None
    )
    # TODO factoiry to set {} as default
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
            if self.vagrantfile_dest is None:
                raise ValueError(
                    "Either vagrantfile or vagrantfile_dest should be defined"
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

    @vagrantfile_dest.validator
    def _check_vagrantfile_dest(self, attribute, value):
        if value is None:
            return
        # TODO check that it's possible to creat it

    def __attrs_post_init__(self):
        if self.hostname is None:
            self.hostname = safe_hostname(self.name)

        # create vagrantfile if missed using template
        if self.vagrantfile is None:
            self.vagrantfile_dest.touch()
            self.vagrantfile = self.vagrantfile_dest
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
        self.last_status = {}

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
                self._localhost.run('VBoxManage unregistervm --delete {}'.format(self.name))

        return self._vagrant.up(*args)

    def destroy(self, ok_if_missed=True, force=True):
        self.destroy_by_name(self.name, ok_if_missed=ok_if_missed, force=force)

    @staticmethod
    def destroy_by_name(machine_name, ok_if_missed=True, force=True):
        _args = ['--force'] if force else []
        vagrant = Vagrant()
        try:
            vagrant.destroy(*_args, machine_name)
        except VagrantError as exc:
            # TODO custom error for that case
            if (
                "machine with the name '{}' was not found configured"
                .format(machine_name) in exc.stderr
            ):
                if ok_if_missed:
                    logger.info(
                        'Vagrant machine with name {} is missed'.format(machine_name)
                    )
                    return
                else:
                    raise RemoteNotExist(machine_name)
            raise

    def cmd(self, cmd, *args):
        return self._vagrant.cmd(cmd, *args)

    def status(self, *args, update=False):
        if not self.last_status or update:
            raw_status = self._vagrant.cmd('status', *args, parse=True)
            self.last_status.clear
            for row in raw_status:
                # TODO possible other cases: empty target and 'ui' as type
                if row.target == self.name:
                    self.last_status[row.data_type] = row.data

        return self.last_status


@attr.s
class VagrantBox:
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


# just some common sense for now
re_filename = re.compile(r'([^a-zA-Z0-9_.-])')
def safe_filename(name):
    return re_filename.sub(r'_', name)


re_remote_non_sanitized = re.compile(r'([^a-zA-Z0-9])')
def sanitize_remote_name_part(name):
    return re_remote_non_sanitized.sub(r'', name)


# TODO
# - tests
# - check chars at the beginning and end
re_unsafe_remote_chars = re.compile(r'([^a-zA-Z0-9_.-])')
def safe_remote_name(name):
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
re_container_name = re.compile(r'([^a-zA-Z0-9_.-])')
def safe_docker_container_name(name):
    return re_container_name.sub(r'_', name)[-MAX_REMOTE_NAME_LEN:]


# TODO
# - reasearch real limitations
# - test
def safe_vagrant_machine_name(name):
    return safe_docker_container_name(name)


# TODO
# - tests
# - better satisfy RFC 1123 (https://tools.ietf.org/html/rfc1123#page-13)
# - ??? actually docker used to check hostnames but is not clear how it happens now
#   (https://github.com/moby/moby/issues/20371, https://github.com/moby/moby/pull/20566)
re_hostname = re.compile(r'([^a-zA-Z0-9-])')
re_multiple_dahses = re.compile(r'-+')
def safe_hostname(name):
    _s = re_hostname.sub('-', name)
    return re_multiple_dahses.sub('-', _s).lower()[-63:].lstrip('-')


def mock_system_cmd(host, cmd, bin_path='/usr/local/bin'):
    # TODO might not work in some cases
    cmd_orig = host.run('which {}'.format(cmd))
    if cmd_orig.rc == 0:
        cmd_orig = cmd_orig.stdout.strip()
        host.check_output('mv -f {0} {0}.bak'.format(cmd_orig))

    # TODO shell quotes interpreting might impact expected output
    cmd_mock = (
        '#!/bin/bash\n'
        'echo {}-ARGS: "$@"'
    ).format(cmd.upper())
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


def fixture_builder(scope, name_with_scope=True, suffix=None, module_name=__name__):

    scopes = scope if type(scope) in (list, tuple) else [scope]

    def _builder(f):
        res = []
        mod = sys.modules[module_name]

        for _scope in scopes:
            name_parts = [
                part for part in (
                    f.__name__, _scope if name_with_scope else None, suffix
                ) if part
            ]
            _f = pytest.fixture(scope=_scope)(f)
            setattr(_f, '__name__', '_'.join(name_parts))
            setattr(mod, _f.__name__, _f)
            res.append(_f)
        return res if scopes is scope else res[0]

    return _builder


def _docker_image_build(client, dockerfile, ctx, image_name):
    # build image from the Dockerfile
    output = []
    try:
        image, output = client.images.build(
            dockerfile=dockerfile, path=ctx, tag=image_name
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


def _docker_container_run(client, image, base_name):
    base_name = base_name[-(MAX_REMOTE_NAME_LEN-3):]

    for i in range(3):  # just three tries
        _id = randrange(100)
        container_name = '{}_{:02d}'.format(base_name, _id)
        try:
            container = client.containers.run(
                image,
                name=container_name,
                # it's safer to not exceed 64 chars on Unix systems for the hostname
                # (real limit might be get using `getconf HOST_NAME_MAX`)
                hostname=safe_hostname(container_name),
                detach=True,
                tty=True,
                # network=network_name,
                volumes={'/sys/fs/cgroup': {'bind': '/sys/fs/cgroup', 'mode': 'ro'}},
                # security_opt=['seccomp=unconfined'],
                tmpfs={'/run': '', '/run/lock': ''},
                ports={'22/tcp': None}
            )
            return Container(container)
        except docker.errors.APIError as exc:
            Container.destroy_by_name(container)

            if 'is already in use' in str(exc):
                # TODO ? try to remove is it's not running
                logger.warning(
                    'container with name {} is already in use'.format(container_name)
                )
            else:
                raise
    else:
        raise RuntimeError(
            "unexpected number of containers with base name {} are already in use"
            .format(base_name)
        )


def _vagrant_machine_up(tmpdir, box, base_name):
    # TODO copy-paste (docker routine)
    base_name = base_name[-(MAX_REMOTE_NAME_LEN-3):]

    for i in range(3):  # just three tries
        _id = randrange(100)
        machine_name = '{}_{:02d}'.format(base_name, _id)
        vagrantfile_dest = tmpdir / 'Vagrantfile.{}'.format(machine_name)
        machine = VagrantMachine(
            machine_name, box=box, vagrantfile_dest=str(vagrantfile_dest)
        )
        try:
            machine.up()
        except VagrantAlreadyInUseError:
            logger.warning(
                'ivagrant machine with name {} is already in use'.format(machine_name)
            )
        else:
            return machine
    else:
        raise RuntimeError(
            "unexpected number of containers with base name {} are already in use"
            .format(base_name)
        )



# TODO use object proxy for testinfra's host instances instead
def run(host, script, force_dump=False):
    res = None
    try:
        res = host.run(script)
    finally:
        if (res is not None) and ((res.rc != 0) or force_dump):
            for line in res.stdout.split(os.linesep):
                logger.debug(line)
            for line in res.stderr.split(os.linesep):
                logger.error(line)
    return res


def check_output(host, script):
    res = run(host, script)
    assert res.rc == 0
    return res.stdout


def inject_repo(localhost, host, ssh_config, project_path, host_repo_dir=None):
    if host_repo_dir is None:
        host_repo_dir = Path('/tmp') / project_path.name
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
                    ('.git', 'files', 'pillar', 'srv', 'cli', 'build')
                ]
            ),
            hostname,
            host_repo_dir
        )
    )
    return host_repo_dir
