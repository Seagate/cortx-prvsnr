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
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

from .command import Command
from provisioner.salt import cmd_run, StatesApplier, local_minion_id
from cortx_setup import config
from provisioner.commands import PillarSet
from provisioner.config import (
    PRVSNR_USER_LOCAL_PILLAR_DIR,
    PRVSNR_DATA_ROOT_DIR,
    PRVSNR_FACTORY_PROFILE_DIR
)
import json
import provisioner


class PillarSync(Command):

    def run(self, **kwargs):

        self.provisioner = provisioner
        if 'username' in kwargs:
            self.provisioner.auth_init(kwargs['username'], kwargs['password'])

        self.logger.debug("Updating pillar data")
        for pillar in config.local_pillars:
            res_pillar = {}
            res = cmd_run(
                f"salt-call --local pillar.get {pillar} --out=json",
                **kwargs
            )
            for key, value in res.items():
                value = json.loads(value)
                value = value['local']
                if pillar == 'cluster' and value.get('srvnode-0'):
                    value[key] = value.pop('srvnode-0')
                if pillar == 'storage' and value.get('enclosure-0'):
                    enc_num = key.split('-')
                    value[f'enclosure-{enc_num[1]}'] = value.pop('enclosure-0')
                res_pillar.update(value)
            self.logger.info(f"Updating {pillar} pillar data")
            self.provisioner.pillar_set(
                f'{pillar}',
                res_pillar
            )
        conf_path = str(PRVSNR_FACTORY_PROFILE_DIR / 'confstore')
        # backup local consftore data
        self.logger.debug(f"Copy local confstore file to {conf_path}")
        conf_create = 'components.provisioner.confstore_create'
        StatesApplier.apply([conf_create], targets=local_minion_id(), **kwargs)

        conf_copy = 'components.provisioner.confstore_copy'
        StatesApplier.apply([conf_copy])
        # backup local pillar data
        cmd_run(f"rm -rf {PRVSNR_DATA_ROOT_DIR}/.backup || true",  **kwargs)
        cmd_run(f"mkdir -p {PRVSNR_DATA_ROOT_DIR}/.backup",  **kwargs)
        cmd_run(f"mv {PRVSNR_USER_LOCAL_PILLAR_DIR}/* "
                f"{PRVSNR_DATA_ROOT_DIR}/.backup/ || true",  **kwargs)
