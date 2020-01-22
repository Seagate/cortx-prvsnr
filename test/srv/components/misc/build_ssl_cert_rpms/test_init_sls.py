import pytest

import logging

from test.helper import PRVSNR_REPO_INSTALL_DIR

logger = logging.getLogger(__name__)


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.hosts(['eosnode1', 'eosnode2'])
def test_build_ssl_cert_rpms_appliance(
    mhosteosnode1, mhosteosnode2, eos_hosts, configure_salt, accept_salt_keys
):
    # enable cluster setup
    # TODO improve later once we have more flexible state parametrization per roles
    mhosteosnode1.check_output(
        "sed -i 's/# - eosnode-2/- eosnode-2/g' {}".format(
            PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / 'cluster.sls'
        )
    )
    mhosteosnode1.check_output(
        "sed -i 's/type: single/type: ees/g' {}".format(
            PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / 'cluster.sls'
        )
    )

    mhosteosnode1.check_output(
        "salt '*' state.apply components.system.config.setup_ssh"
    )

    for label in ('eosnode1', 'eosnode2'):
        mhosteosnode1.check_output(
            "salt '{}' state.apply components.misc.build_ssl_cert_rpms".format(
                eos_hosts[label]['minion_id']
            )
        )

    # TODO check expected changes on nodes
