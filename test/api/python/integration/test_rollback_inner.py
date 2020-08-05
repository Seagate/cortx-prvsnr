#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
