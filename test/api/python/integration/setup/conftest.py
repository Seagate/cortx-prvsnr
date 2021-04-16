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

import pytest
from pathlib import Path
from collections import defaultdict
from copy import deepcopy
from typing import Optional, Union

from provisioner.vendor import attr
from provisioner import inputs, utils

from . helper import (
    RunT, ScaleFactorT, SourceT,
    create_hosts, set_root_passwd
)


@attr.s(auto_attribs=True)
class SetupOpts(inputs.ParserMixin):
    parser_prefix = 'setup-'

    interactive: bool = attr.ib(
        default=False,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "do interactive break before run",
                'metavar': 'PATH'
            }
        }
    )
    logdir: Optional[Union[str, Path]] = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "logdir to mount inside the container",
                'metavar': 'PATH'
            }
        },
        converter=utils.converter_path_resolved,
        validator=attr.validators.optional(
            utils.validator_dir_exists
        )
    )
    cortx_iso: Optional[Union[str, Path]] = attr.ib(
        default=None,
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "path to CORTX deploy ISO",
                'metavar': 'PATH'
            }
        },
        converter=utils.converter_path_resolved,
        validator=attr.validators.optional(
            utils.validator_path_exists
        )
    )


@pytest.fixture(scope='session')
def custom_opts_t():
    return SetupOpts


@pytest.fixture(scope='session')
def root_passwd():
    return 'root'


@pytest.fixture(scope='module')
def env_level():
    return 'setup'


@pytest.fixture
def env_provider():
    return 'docker'


@pytest.fixture(params=ScaleFactorT)
def hosts_num(request):
    return request.param.value


@pytest.fixture(params=[RunT.REMOTE_CLI, RunT.ONTARGET_CLI])
def setup_mode_cli(request):
    return request.param


@pytest.fixture(params=[True, False], ids=['HA', 'noHA'])
def ha(request, hosts_num):
    if hosts_num < 2 and request.param:
        pytest.skip()
    else:
        return request.param


@pytest.fixture
def setup_hosts(request, hosts_num, root_passwd, mlocalhost):
    mhosts = create_hosts(request, hosts_num)
    set_root_passwd(mhosts, root_passwd)
    return mhosts


@pytest.fixture
def run_host(request, setup_mode_cli, setup_hosts):
    return (
        request.getfixturevalue('mlocalhost')
        if setup_mode_cli == RunT.REMOTE_CLI else
        setup_hosts[0]
    )


@pytest.fixture
def cli_log_args(
    request, setup_mode_cli, logdir_host,
    safe_function_name, custom_opts, tmpdir_function,
):
    logfile = None
    if setup_mode_cli == RunT.REMOTE_CLI:
        if custom_opts.logdir:
            logfile = (
                custom_opts.logdir
                / safe_function_name.with_suffix('.setup.log')
            )
        else:
            logfile = tmpdir_function / 'setup.log'
    elif logdir_host:
        logfile = logdir_host / safe_function_name.with_suffix('.setup.log')

    return f"--logfile --logfile-filename {logfile}" if logfile else ''


@pytest.fixture
def setup_hosts_specs(setup_hosts):
    return [
        f"srvnode-{i + 1}:{mhost.ssh_host}"
        for i, mhost in enumerate(setup_hosts)
    ]


@pytest.fixture
def cli_args(
    source, ha, cli_log_args, setup_hosts_specs, run_host, custom_opts
):
    cmd = ['--source', source.value]

    if source == SourceT.LOCAL and setup_mode_cli == RunT.ONTARGET_CLI:
        cmd.extend(['--local-repo', run_host.repo])
    elif source == SourceT.ISO:
        cmd.extend(['--iso-cortx', str(custom_opts.cortx_iso)])

    if ha:
        cmd.append('--ha')

    cmd.append('--pypi-repo')

    cmd.append(cli_log_args)
    cmd.extend(setup_hosts_specs)

    return ' '.join(cmd)


@pytest.fixture
def cli_cmd(
    setup_mode_cli, cli_args, root_passwd
):
    return f"SSHPASS={root_passwd} provisioner setup_provisioner {cli_args}"


@pytest.fixture(params=SourceT)
def source(request, custom_opts):
    if request.param == SourceT.ISO and not custom_opts.cortx_iso:
        pytest.skip()
    else:
        return request.param


@pytest.fixture
def logdir_host(tmpdir_function, custom_opts):
    return (
        None if custom_opts.logdir is None else
        tmpdir_function / custom_opts.logdir.name
    )


@pytest.fixture
def hosts_spec(hosts_spec, hosts, tmpdir_function, custom_opts, logdir_host):
    res = deepcopy(hosts_spec)
    for host in hosts:
        host_glusterfs = tmpdir_function / host / 'srv/glusterfs'
        host_glusterfs.mkdir(parents=True)

        docker_settings = res[host]['remote']['specific']
        docker_settings['docker'] = defaultdict(
            dict, docker_settings.get('docker', {})
        )
        docker_settings = docker_settings['docker']
        docker_settings['privileged'] = True

        docker_settings['volumes'][str(host_glusterfs)] = {
            'bind': '/srv/glusterfs', 'mode': 'rw'
        }
        docker_settings['volumes']['/dev'] = {
            'bind': '/dev', 'mode': 'ro'
        }
        if custom_opts.logdir:
            docker_settings['volumes'][
                str(custom_opts.logdir)
            ] = {'bind': str(logdir_host), 'mode': 'rw'}
    return res


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if (
            hasattr(item, 'callspec')
            and item.callspec.params.get('source') == SourceT.LOCAL
            and item.callspec.params.get('ha')
            and item.callspec.params.get('hosts_num') == ScaleFactorT.SINGLE
        ):
            item.add_marker(pytest.mark.verified)
