import pytest
import logging

from test.helper import install_provisioner_api

logger = logging.getLogger(__name__)


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_yum_rollback_manager(
    mhosteosnode1, run_test, eos_hosts
):
    install_provisioner_api(mhosteosnode1)
    run_test(mhosteosnode1, env={
        'TEST_MINION_ID': eos_hosts['eosnode1']['minion_id']
    })
