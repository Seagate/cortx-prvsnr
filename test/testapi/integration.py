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

import logging
from pathlib import Path

import pytest

from provisioner.vendor import attr
from provisioner import config
from provisioner.commands._basic import RunArgsSaltClient
from provisioner.commands.helper import (
    SSHProfileGenerator, EnsureNodesReady
)
from provisioner.resources.saltstack import (
    SaltClusterConfig,
    SaltMasterStart,
    SaltMinionStart
)
from provisioner.resources.provisioner import (
    ProvisionerInstallLocal,
    ProvisionerAPIInstall
)

from provisioner.scm.saltstack.rc_sls.saltstack import (
    SaltClusterConfigSLS,
    SaltMasterStartSLS,
    SaltMinionStartSLS
)
from provisioner.scm.saltstack.rc_sls.provisioner import (
    ProvisionerInstallLocalSLS,
    ProvisionerAPIInstallSLS
)

from test import helper as h

from . import defs
from . import helper

logger = logging.getLogger(__name__)


@attr.s
class HostMeta:
    # TODO validators for all
    remote = attr.ib()
    host = attr.ib()
    ssh_config = attr.ib()
    request = attr.ib()

    label = attr.ib(converter=lambda v: '' if not v else v, default='')
    machine_name = attr.ib(default=None)
    interface = attr.ib(default=None)
    host_user = attr.ib(default=None)

    _hostname = attr.ib(init=False, default=None)
    _tmpdir = attr.ib(init=False, default=None)
    _repo = attr.ib(init=False, default=None)
    _local_user_home = attr.ib(init=False, default=None)
    _api_installed = attr.ib(init=False, default=False)
    _rpm_prvsnr = attr.ib(init=False, default=None)
    _rpm_prvsnr_cli = attr.ib(init=False, default=None)
    _rpm_prvsnr_api = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        # TODO more smarter logic to get interface that is asseccible from host
        # (relates to https://github.com/hashicorp/vagrant/issues/2779)
        if self.interface is None:
            if (
                isinstance(self.remote, h.VagrantMachine) and
                (self.remote.provider == 'vbox')
            ):
                self.interface = 'enp0s8'
            else:
                self.interface = 'eth0'

        assert self.host.interface(self.interface).exists

    @property
    def hostname(self):
        if self._hostname is None:
            self._hostname = self.host.check_output('hostname')
        return self._hostname

    @property
    def ssh_host(self):
        return self.host.interface(self.interface).addresses[0]

    @property
    def tmpdir(self):
        if self._tmpdir is None:
            tmpdir_function = self.request.getfixturevalue('tmpdir_function')
            # TODO non linux systems
            self._tmpdir = (
                Path('/tmp') / tmpdir_function.relative_to('/')  # nosec
            )
            self.host.check_output("mkdir -p {}".format(self._tmpdir))
        return self._tmpdir

    def copy_from_host(self, host_path, local_path=None):
        tmpdir_local = self.request.getfixturevalue('tmpdir_function')

        if local_path is None:
            local_path = tmpdir_local / host_path.name
        else:
            local_path = local_path.resolve()
            # ensure that it's inside tmpdir
            local_path.relative_to(tmpdir_local)

        local_path.parent.mkdir(parents=True, exist_ok=True)

        h.localhost.check_output(
            "scp -r -F {} {}:{} {}".format(
                self.ssh_config,
                self.hostname,
                host_path,
                local_path
            )
        )
        return local_path

    def copy_to_host(self, local_path, host_path=None):
        if host_path is None:
            host_path = self.tmpdir / local_path.name

        self.host.check_output(
            "mkdir -p {}".format(host_path.parent)
        )

        h.localhost.check_output(
            "scp -r -F {} {} {}:{}".format(
                self.ssh_config,
                local_path,
                self.hostname,
                host_path
            )
        )
        return host_path

    @property
    def rpm_prvsnr(self):
        if self._rpm_prvsnr is None:
            rpm_local_path = self.request.getfixturevalue('rpm_prvsnr')
            self._rpm_prvsnr = self.copy_to_host(rpm_local_path)
        return self._rpm_prvsnr

    @property
    def rpm_prvsnr_cli(self):
        if self._rpm_prvsnr_cli is None:
            rpm_local_path = self.request.getfixturevalue('rpm_prvsnr_cli')
            self._rpm_prvsnr_cli = self.copy_to_host(rpm_local_path)
        return self._rpm_prvsnr_cli

    @property
    def rpm_prvsnr_api(self):
        if self._rpm_prvsnr_api is None:
            rpm_local_path = self.request.getfixturevalue('rpm_prvsnr_api')
            self._rpm_prvsnr_api = self.copy_to_host(rpm_local_path)
        return self._rpm_prvsnr_api

    @property
    def repo(self):
        if self._repo is None:
            repo_tgz = self.request.getfixturevalue('repo_tgz')
            self._repo = h.inject_repo(
                self.host, self.ssh_config, repo_tgz
            )
        return self._repo

    def api_installed(self, local_user=False):
        if not self._api_installed:
            logger.info(
                f"Installing API on {self.hostname}"
            )
            self.check_output(
                (
                    f"LC_ALL=en_US.UTF-8"
                    f" pip3 install --user {self.repo / 'api/python'}"
                ),
                local_user=local_user
            )
            self._api_installed = True

    @property
    def fixture_name(self):
        return 'mhost' + self.label

    def run(self, script, *args, force_dump=False, **kwargs):
        return h.run(self.host, script, *args, force_dump=force_dump, **kwargs)

    def check_output(
        self, script, *args, force_dump=False, local_user=False,
        **kwargs
    ):
        if local_user and not self.host_user:
            raise RuntimeError(
                "connection for local user is not available"
                f" for {self.remote.name}"
            )

        if local_user:
            _host = self.host_user
            script = f"source ~/.bash_profile; {script}"
        else:
            _host = self.host

        return h.check_output(
            _host, script, *args, force_dump=force_dump, **kwargs
        )


@pytest.fixture
def root_passwd():
    return defs.ROOT_PASSWD


@pytest.fixture(scope='module')
def hosts_num_module(request):
    return defs.ScaleFactorT.SINGLE.value


@pytest.fixture
def hosts_num(request, hosts_num_module):
    marker = request.node.get_closest_marker('hosts_num')
    if marker:
        return marker.args[0]
    else:
        return hosts_num_module


@pytest.fixture
def setup_hosts(request, hosts_num, root_passwd, mlocalhost):
    mhosts = helper.create_hosts(request, hosts_num)
    helper.set_root_passwd(mhosts, root_passwd)
    return mhosts


@pytest.fixture
def setup_hosts_specs(setup_hosts):
    return [
        f"srvnode-{i + 1}:{mhost.ssh_host}"
        for i, mhost in enumerate(setup_hosts)
    ]


@pytest.fixture
def ssh_profile(tmpdir_function):
    profile = tmpdir_function / 'ssh_profile'
    SSHProfileGenerator(profile=profile).run()
    return profile


@pytest.fixture
def ensure_ready(ssh_profile, ssh_key, setup_hosts_specs):
    EnsureNodesReady(
        nodes=setup_hosts_specs, profile=ssh_profile, ssh_key=ssh_key
    ).run()


@pytest.fixture
def ssh_client(ssh_profile, ssh_key, setup_hosts_specs, ensure_ready):
    return RunArgsSaltClient(
        salt_client_type='ssh',
        salt_ssh_profile=ssh_profile
    ).client


@pytest.fixture
def salt_configured(ssh_client):
    SaltClusterConfigSLS(
        state=SaltClusterConfig(
            onchanges_minion='stop',
            onchanges_master='restart',
        ),
        client=ssh_client
    ).run()


@pytest.fixture
def salt_ready(ssh_client, salt_configured):
    SaltMasterStartSLS(
        state=SaltMasterStart(),
        client=ssh_client
    ).run()

    SaltMinionStartSLS(
        state=SaltMinionStart(),
        client=ssh_client
    ).run()

    # TODO ensure minions are ready


@pytest.fixture
def provisioner_installed(ssh_client):
    ProvisionerInstallLocalSLS(
        state=ProvisionerInstallLocal(),
        client=ssh_client
    ).run()


@pytest.fixture
def provisioner_api_installed(ssh_client, provisioner_installed):
    ProvisionerAPIInstallSLS(
        state=ProvisionerAPIInstall(api_distr='pip'),
        client=ssh_client
    ).run()


@pytest.fixture
def cortx_mocks_deployed(
    ssh_client, salt_configured, provisioner_installed
):
    ssh_client.cmd_run(
        "salt '*' state.apply components.misc_pkgs.mocks.cortx",
        targets=ssh_client.roster_targets[0]
    )


@pytest.fixture
def cortx_upgrade_iso_mock_path():
    return config.PRVSNR_DATA_LOCAL_DIR / 'cortx_repos/upgrade_mock_2.1.0.iso'


@pytest.fixture
def cortx_upgrade_iso_mock(
    ssh_client,
    cortx_upgrade_iso_mock_path,
    salt_configured,
    provisioner_installed
):
    ssh_client.cmd_run(
        "salt '*' state.apply components.misc_pkgs.mocks.cortx.build_upgrade",
        targets=ssh_client.roster_targets[0]
    )
    return cortx_upgrade_iso_mock


@pytest.fixture
def cortx_upgrade_iso_mock_installed(
    ssh_client,
    cortx_upgrade_iso_mock,
    provisioner_api_installed
):
    ssh_client.provisioner_cmd(
        'set_swupgrade_repo',
        fun_args=[cortx_upgrade_iso_mock],
        targets=ssh_client.roster_targets[0]
    )
