import os
import pytest
import json

import logging

from test.helper import PRVSNR_REPO_INSTALL_DIR

logger = logging.getLogger(__name__)

# TODO might makes sense to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.hosts(['eosnode1'])
@pytest.mark.env_level('salt-installed')
@pytest.mark.skip(reason="EOS-4907")
def test_setup_ssh_known_hosts(
    mhosteosnode1, eos_hosts, configure_salt, accept_salt_keys
):
    minion_id = eos_hosts['eosnode1']['minion_id']

    mhosteosnode1.check_output(
        "salt '{}' state.apply components.system.config.setup_ssh".format(
            minion_id
        )
    )

    output = mhosteosnode1.check_output('salt-call --local --out json config.get master')
    master_host = json.loads(output)['local']

    # TODO checks for the keys' types
    mhosteosnode1.check_output('ssh-keygen -F {}'.format(minion_id))
    mhosteosnode1.check_output('ssh-keygen -F {}'.format(master_host))
