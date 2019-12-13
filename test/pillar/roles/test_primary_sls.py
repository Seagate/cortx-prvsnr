import os
import pytest
import json
from pathlib import Path

import logging
import testinfra

from test.helper import PRVSNR_REPO_INSTALL_DIR

logger = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def env_name():
    return 'centos7-salt-installed'


# TODO might makes sense to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
@pytest.mark.env_name('centos7-salt-installed')
def test_mine_functions_primary_host_keys(
    mhosteosnode1, eos_hosts, configure_salt, accept_salt_keys
):
    def _make_data_comparable(data):
        data = [
            {k: v for k, v in litem.items() if k != 'hostname'}
            for litem in data
        ]
        return sorted(data, key=lambda k: k['enc'])

    mine_function_alias = 'primary_host_keys'
    minion_id = eos_hosts['eosnode1']['minion_id']

    output = mhosteosnode1.check_output(
        "salt '{}' --out json mine.get 'roles:primary' '{}' grain".format(
            minion_id, mine_function_alias
        )
    )
    mined = json.loads(output)[minion_id]
    assert [minion_id] == list(mined.keys())
    mined = _make_data_comparable(mined[minion_id])

    output = mhosteosnode1.check_output(
        "salt '{}' --out json ssh.recv_known_host_entries 127.0.0.1".format(
            minion_id
        )
    )
    expected = _make_data_comparable(json.loads(output)[minion_id])

    assert expected == mined
