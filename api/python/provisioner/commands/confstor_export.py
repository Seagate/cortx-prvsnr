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

import logging

from pathlib import Path
from collections.abc import Mapping
from typing import Type
from cortx.utils.ConfStore import Conf
from provisioner.salt import local_minion_id
from provisioner.vendor import attr
from ..salt import StateFunExecuter


from . import (
    CommandParserFillerMixin
)

from ..config import (
    PRVSNR_GEN_CONFIG_DIR
)

from .. import (
    inputs
)

from .pillar import (
    PillarResolver,
    PillarKey
)

from ..utils import (
    load_yaml
)

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ConfstorExport(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    description = "Export pillar template data to confstor"

    @staticmethod
    def _get_keys(obj, string=''):
        """
        This function returns all the nested keypaths along with
        values in the dictionary.

        """
        for key, value in obj.items():
            if isinstance(obj, Mapping):
                if string:
                    yield from _get_keys(value, f"{key}")
                else:
                    yield from _get_keys(value, f"{string}>{key}")
            else:
                yield (f"{string}>{key}", "{value}")

    def run(self):
        """
        Confstor_export command execution method.
        It creates a pillar template and loads into the confstor
        of which the path specified in pillar
        """

        try:
            Path(PRVSNR_GEN_CONFIG_DIR).mkdir(parents=True, exist_ok=True)
            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name=PRVSNR_GEN_CONFIG_DIR +
                    '/confstor_template.sls',
                    source='salt://components/system/files/confstor_template.yml.j2',
                    template='jinja'))
            logger.info("Pillar confstor template is created at "
                        f"'{PRVSNR_GEN_CONFIG_DIR}'/confstor_template.sls"
                        )
        except Exception as exc:
            logger.exception(
                f"Unable to create confstor template due to {exc}")

        try:

            yaml_dict = load_yaml(PRVSNR_GEN_CONFIG_DIR +
                                  '/confstor_template.sls')
            pillar_confstor_path = "provisioner/common_config/confstore_url"
            pillar_key = PillarKey(pillar_confstor_path)
            pillar = PillarResolver(local_minion_id()).get([pillar_key])
            pillar = next(iter(pillar.values()))

            #Path(CORTX_CONFIG_DIR).mkdir(parents=True, exist_ok=True)

            Conf.load('provisioner', pillar[PillarKey(pillar_key)])

            for key, value in _get_keys(yaml_dict, ""):
                Conf.set("provisioner", key, value)
            logger.info("Template loaded to confstor")

        except Exception as exc:
            logger.exception(f"Unable to load template due to {exc}")
