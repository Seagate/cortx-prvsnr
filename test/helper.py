import sys
import re
from copy import deepcopy
from pathlib import Path

import pytest
from functools import wraps

import logging
logger = logging.getLogger(__name__)

PRVSNR_REPO_INSTALL_DIR = Path('/opt/seagate/eos-prvsnr')

# just some common sense for now
re_filename = re.compile(r'([^a-zA-Z0-9_.-])')
def safe_filename(name):
    return re_filename.sub(r'_', name)


# TODO
# - tests
# - check chars at the beginning and end
re_container_name = re.compile(r'([^a-zA-Z0-9_.-])')
def safe_docker_container_name(name):
    return re_container_name.sub(r'_', name)


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
                    f.__name__, suffix, _scope if name_with_scope else None
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


def _docker_container_run(client, image, container_name):
    return client.containers.run(
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
