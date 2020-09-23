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

import os
import pytest

from provisioner.salt import YumRollbackManager, cmd_run
from provisioner import errors


# TODO check for ValueError on multiple targets
def test_yum_rollback_manager():
    minion_id = os.environ['TEST_MINION_ID']

    some_minion_id = 'some_minion_id'
    with pytest.raises(errors.SaltNoReturnError) as excinfo:
        with YumRollbackManager(some_minion_id) as rb_manager:
            pass

    with pytest.raises(ValueError) as excinfo:
        with YumRollbackManager(minion_id) as rb_manager:
            assert minion_id in rb_manager.last_txn_ids
            cmd_run('yum install -y vim', minion_id)
            cmd_run('rpm -qi vim-enhanced', minion_id)
            raise ValueError('some error')

    assert str(excinfo.value) == 'some error'

    with pytest.raises(errors.SaltError):
        cmd_run('rpm -qi vim-enhanced', minion_id)
