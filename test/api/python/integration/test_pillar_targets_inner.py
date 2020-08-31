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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

import os
import logging
import pytest

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
    with pytest.raises(provisioner.errors.SaltNoReturnError):
        pu.apply()
    pr = PillarResolver(targets=minion_id)
    get_res = pr.get([ntp_server_param])
    #  value for minion_1 is not changed
    assert get_res[minion_id][ntp_server_param] == value_minion_1
