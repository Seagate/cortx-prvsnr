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
import re
from pathlib import Path

import pytest
from unittest.mock import patch, MagicMock
import yaml

from provisioner.commands.upgrade import GetSWUpgradeInfo, SetSWUpgradeRepo
from provisioner.config import ReleaseInfo, SWUpgradeInfoFields

from .test_validator import RELEASE_INFO

BASE_DIR = Path('/opt/seagate/upgrade/')
LOCAL_MINION_ID = 'srvnode-1'

RPM_NAME_REGEX = re.compile(r'^([0-9a-zA-Z\-_]+)-([0-9\-.]+)\..*.rpm$')


def get_packages_versions():
    res = list()
    components = yaml.safe_load(RELEASE_INFO)[ReleaseInfo.COMPONENTS.value]
    for package in components:
        package_name, version = RPM_NAME_REGEX.search(package).groups()
        res.append(f'{package_name} {version}')

    return {LOCAL_MINION_ID: '\n'.join(res)}


def get_cortx_packages():
    res = get_packages_versions()
    packages = res[LOCAL_MINION_ID].strip().split('\n')

    res = dict()
    for entry in packages:
        pkg, ver = entry.split(" ")
        res[pkg] = {SWUpgradeInfoFields.VERSION.value: ver}

    return res


class LockMock:

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        """

        Returns
        -------

        """
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """

        Parameters
        ----------
        exc_type:
            Exception type
        exc_val:
            Exception value
        exc_tb:
            Exception traceback

        Returns
        -------

        """
        pass


@pytest.mark.unit
def test_get_swupgrade_info():
    """
    Test for Provisioner wrapper over HA cluster stop command.

    Returns
    -------

    """
    local_minion_id1 = ('provisioner.commands.upgrade.'
                        'get_swupgrade_info.local_minion_id')
    local_minion_id2 = ('provisioner.commands.upgrade.'
                        'set_swupgrade_repo.local_minion_id')
    load_yaml = 'provisioner.commands.upgrade.set_swupgrade_repo.load_yaml'
    cmd_run = 'provisioner.commands.upgrade.set_swupgrade_repo.cmd_run'
    with patch.object(SetSWUpgradeRepo, '_prepare_single_iso_for_apply',
                      new=lambda self, x: None), \
            patch.object(SetSWUpgradeRepo, '_get_mount_dir',
                         new=lambda self: BASE_DIR), \
            patch.object(SetSWUpgradeRepo, '_apply',
                         new=lambda self, x, targets, local: None), \
            patch(local_minion_id1, MagicMock()), \
            patch(local_minion_id2, MagicMock()) as local_minion_id2_mock, \
            patch('provisioner.lock.Lock', LockMock) as api_lock_mock, \
            patch(load_yaml,
                  MagicMock()) as load_yaml_mock, \
            patch(cmd_run, MagicMock()) as cmd_run_mock:
        load_yaml_mock.return_value = yaml.safe_load(RELEASE_INFO)
        api_lock_mock.return_value = lambda fun: fun
        local_minion_id2_mock.return_value = LOCAL_MINION_ID

        cmd_run_mock.return_value = get_packages_versions()

        cortx_info = GetSWUpgradeInfo().run(iso_path='/path/to/single.iso')
        assert cortx_info.metadata == yaml.safe_load(RELEASE_INFO)
        assert cortx_info.packages == get_cortx_packages()
