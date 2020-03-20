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
