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

from pathlib import Path
import yaml
import pytest
import json

import logging

import test.helper as h

logger = logging.getLogger(__name__)


# TODO
#  - might makes sense. to verify for cluster case as well
@pytest.mark.isolated
@pytest.mark.env_provider('vbox')  # mount makes docker inappropriate
@pytest.mark.hosts(['srvnode1'])
@pytest.mark.env_level('salt-installed')
def test_user_pillar(
    mhostsrvnode1, cortx_hosts, configure_salt, accept_salt_keys
):
    minion_id = cortx_hosts['srvnode1']['minion_id']
    test_pillar = {'somekey': {'key1': 'value1', 'key2': 'value2'}}
    pillar_fname = 'release.sls'

    def update_pillar(pillar_data, pillar_path, minion_id='*'):
        mhostsrvnode1.check_output(
            "mkdir -p {}"
            " && echo '{}' >{}"
            " && salt '{}' saltutil.refresh_pillar"
            .format(
                pillar_path.parent,
                yaml.dump(
                    pillar_data, default_flow_style=False, canonical=False
                ),
                pillar_path,
                minion_id
            )
        )

    def get_pillar():
        res = mhostsrvnode1.check_output("salt '*' --out json pillar.items")
        return json.loads(res)

    def check_pillar(update=None):
        if update:
            test_pillar['somekey'].update(update['somekey'])
        pillar = get_pillar()
        assert pillar[minion_id]['somekey'] == test_pillar['somekey']

    # add data any minion default pillar
    pillar_path = h.PRVSNR_PILLAR_DIR / 'components' / pillar_fname
    update_pillar(test_pillar, pillar_path)
    check_pillar()

    # add data any minion user pillar
    update = {'somekey': {'key2': 'value2new', 'key3': 'value3'}}
    pillar_path = h.PRVSNR_USER_PI_ALL_HOSTS_DIR / pillar_fname
    update_pillar(update, pillar_path)
    check_pillar(update)

    # add data to minion's default pillar
    update = {'somekey': {'key3': 'value3new', 'key4': 'value4'}}
    pillar_path = Path(
        h.PRVSNR_DEF_PI_HOST_DIR_TMPL.format(minion_id=minion_id)
    ) / pillar_fname
    update_pillar(update, pillar_path)
    check_pillar(update)

    # add data to minion's user pillar
    update = {'somekey': {'key4': 'value4new', 'key5': 'value5'}}
    pillar_path = Path(
        h.PRVSNR_USER_PI_HOST_DIR_TMPL.format(minion_id=minion_id)
    ) / pillar_fname
    update_pillar(update, pillar_path)
    check_pillar(update)

    minion_id_2 = minion_id + '_2'
    # add data to another minion's default pillar
    update = {'somekey': {'key5': 'value5new'}}
    pillar_path = Path(
        h.PRVSNR_DEF_PI_HOST_DIR_TMPL.format(minion_id=minion_id_2)
    ) / pillar_fname
    update_pillar(update, pillar_path)
    check_pillar()

    # add data to another minion's user pillar
    update = {'somekey': {'key5': 'value5newnew'}}
    pillar_path = Path(
        h.PRVSNR_USER_PI_HOST_DIR_TMPL.format(minion_id=minion_id_2)
    ) / pillar_fname
    update_pillar(update, pillar_path)
    check_pillar()
