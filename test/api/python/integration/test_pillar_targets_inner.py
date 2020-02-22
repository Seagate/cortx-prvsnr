import os
import logging

import provisioner
from provisioner.pillar import PillarUpdater, PillarResolver
from provisioner.inputs import NTP

logger = logging.getLogger(__name__)


def test_pillar_targets():
    minion_id = os.environ['TEST_MINION_ID']
    ntp_server_param = NTP.param_spec('server')

    # add data for all minions group user pillar
    pu = PillarUpdater(targets=provisioner.ALL_MINIONS)
    pr = PillarResolver(targets=provisioner.ALL_MINIONS)
    value_all = '1.2.3.4'
    pu.update(NTP(server=value_all))
    pu.apply()
    get_res = pr.get([ntp_server_param])
    assert get_res[minion_id][ntp_server_param] == value_all

    # add data to minion's user pillar
    pu = PillarUpdater(targets=minion_id)
    pr = PillarResolver(targets=minion_id)
    value_minion_1 = '1.2.3.5'
    pu.update(NTP(server=value_minion_1))
    pu.apply()
    get_res = pr.get([ntp_server_param])
    assert get_res[minion_id][ntp_server_param] == value_minion_1

    # add data to another minion's user pillar
    minion_id_2 = minion_id + '_2'
    pu = PillarUpdater(targets=minion_id_2)
    value_minion_2 = '1.2.3.6'
    pu.update(NTP(server=value_minion_2))
    pu.apply()
    pr = PillarResolver(targets=minion_id)
    get_res = pr.get([ntp_server_param])
    #  value for minion_1 is not changed
    assert get_res[minion_id][ntp_server_param] == value_minion_1
