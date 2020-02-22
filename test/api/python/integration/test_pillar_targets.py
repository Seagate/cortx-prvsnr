import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def test_path():
    return 'test/api/python/integration/test_pillar_targets_inner.py'


@pytest.mark.timeout(1200)
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
def test_pillar_targets(
    mhosteosnode1, run_test, eos_hosts
):
    run_test(mhosteosnode1, env={
        'TEST_MINION_ID': eos_hosts['eosnode1']['minion_id']
    })
