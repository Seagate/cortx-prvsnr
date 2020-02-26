import os
import pytest

from provisioner.salt import YumRollbackManager, cmd_run
from provisioner import errors


def test_rollback():
    minion_id = os.environ['TEST_MINION_ID']

    with pytest.raises(ValueError):
        with YumRollbackManager(minion_id) as rb_manager:
            assert minion_id in rb_manager.last_txn_ids
            cmd_run('yum install -y vim', minion_id)
            cmd_run('rpm -qi vim', minion_id)
            raise ValueError('some error')

    with pytest.raises(errors.SaltError):
        cmd_run('rpm -qi vim', minion_id)
