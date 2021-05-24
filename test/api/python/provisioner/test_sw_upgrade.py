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
from pathlib import Path

import pytest
from unittest.mock import patch, MagicMock
import yaml

from provisioner.commands.upgrade import GetSWUpgradeInfo, SetSWUpgradeRepo

from .test_validator import RELEASE_INFO

BASE_DIR = Path('/opt/seagate/upgrade/')


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
    local_minion_id = ('provisioner.commands.upgrade.'
                       'get_swupgrade_info.local_minion_id')
    load_yaml = 'provisioner.commands.upgrade.set_swupgrade_repo.load_yaml'
    with patch.object(SetSWUpgradeRepo, '_prepare_single_iso_for_apply',
                      new=lambda self, x: None), \
            patch.object(SetSWUpgradeRepo, '_get_mount_dir',
                         new=lambda self: BASE_DIR), \
            patch.object(SetSWUpgradeRepo, '_apply',
                         new=lambda self, x, targets, local: None), \
            patch(local_minion_id, MagicMock()), \
            patch('provisioner.lock.Lock', LockMock) as api_lock_mock, \
            patch(load_yaml,
                  MagicMock()) as load_yaml_mock:
        load_yaml_mock.return_value = yaml.safe_load(RELEASE_INFO)
        api_lock_mock.return_value = lambda fun: fun

        metadata = GetSWUpgradeInfo().run(iso_path='/path/to/single.iso')
        assert metadata == yaml.safe_load(RELEASE_INFO)
