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
import json

from pathlib import Path
from collections.abc import Mapping

from ..config import (
    CORTX_CONFIG_DIR,
    CONFSTORE_CLUSTER_CONFIG,
    PRVSNR_GEN_CONFIG
)

from ..utils import (
    load_yaml
)

from provisioner.api import grains_get
from provisioner.commands import PillarGet
from provisioner.inputs import METADATA_ARGPARSER
from provisioner.salt import local_minion_id
from provisioner.vendor import attr

logger = logging.getLogger(__name__)


class RunArgsPillarExportAttrs:
    export_file: str = attr.ib(
        metadata={
            METADATA_ARGPARSER: {
                'help': "output file to export JSON format of pillar data"
            }
        },
        default=CONFSTORE_CLUSTER_CONFIG
    )


@attr.s(auto_attribs=True)
class RunArgsPillarExport:
    export_file: str = RunArgsPillarExportAttrs.export_file

    def __attrs_post_init__(self):
        pass


@attr.s(auto_attribs=True)
class PillarExport(PillarGet):
    _run_args_type = RunArgsPillarExport


    def _get_keys(self, obj, string=''):
        """
        Method to address ConfStore LIMITATION.

        Currently, ConfStore accepts ONLY string values.
        This can be commented when limitation is addressed.

        Converts all values (arrays, null, bool, int) to string

        """
        for key,value in obj.items():
            if (isinstance(obj, Mapping):
                if string:
                    yield from _get_keys(value,f"{key}")
                else:
                    yield from _get_keys(value,f"{string}>{key}")
            else:
                yield (f"{string}>{key}","{value}")

    def run(
        self,
        *args,
        **kwargs
    ):
        """pillar_export command execution method.

        Keyword arguments:
        *args: Pillar path in <root_node>/child_node format.
        (default: all pillar data)
        **kwargs: accepts the following keys:
            export_file: Output file for pillar dump
        """

        try:
            Path(PRVSNR_GEN_CONFIG_DIR).mkdir(parents=True, exist_ok=True)
            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name=PRVSNR_GEN_CONFIG_DIR + '/confstor_template.sls',
                    source= 'salt://components/system/files/confstor_template.yml.j2',
                    template= 'jinja'
                )
            )
            
            
            yaml_dict = load_yaml(PRVSNR_GEN_CONFIG_DIR + '/confstor_template.sls')
            pillar_confstor_path = "provisioner/common_config/confstore_url"
            pillar_key = PillarKey(pillar_confstor_path)
            pillar = PillarResolver(local_minion_id()).get([pillar_key])
            pillar = next(iter(pillar.values()))
            
            Path(CORTX_CONFIG_DIR).mkdir(parents=True, exist_ok=True)
 
            Conf.load('provisioner',pillar[PillarKey(pillar_key)])

            for key,value in _get_keys(yaml_dict,""):
                Conf.set("provisioner",key,value)


        except Exception as exc:
            raise ValueError(
                  f"Error in translating Pillar data to JSON: {str(exc)}")
