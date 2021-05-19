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
# API to export pillar data to Confstore

import importlib
import logging
from pathlib import Path
from typing import Type
from provisioner.vendor import attr
from provisioner.api import grains_get
from ..salt import (
    StateFunExecuter,
    local_minion_id,
    copy_to_file_roots
)

from . import (
    CommandParserFillerMixin
)

from ..config import (
    ALL_MINIONS,
    CONFSTORE_ROOT_FILE,
    CORTX_CONFIG_DIR
)

from .. import (
    inputs
)

from ..pillar import (
    PillarResolver,
    PillarKey
)

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ConfStoreExport(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    description = "Export pillar template data to ConfStore"

    key_delimiter = ">"
    kv_delimiter = "=>"

    def _confstore_encrypt(self, key, value, cipher):  # noqa: C901
        if not value:
            return value
        cluster_id = grains_get("cluster_id", targets=local_minion_id())[
            local_minion_id()]["cluster_id"]
        component_name = "cortx"
        unique_seed = key.split(self.key_delimiter)[1]

        if "bmc" in key:
            component_name = "cluster"
        elif "storage_enclosure" in key:
            component_name = "storage"
        else:
            unique_seed = cluster_id

        cipher_key = cipher.Cipher.generate_key(cluster_id, component_name)
        try:
            value = cipher.Cipher.decrypt(
                cipher_key, value.encode("utf-8")
            ).decode("utf-8")
        except cipher.CipherInvalidToken:
            logger.warning(f"Decryption for {key} failed as key already decrypted ")

        root_node = key.split(self.key_delimiter)[0]

        cipher_key = cipher.Cipher.generate_key(unique_seed, root_node)
        return str(
            cipher.Cipher.encrypt(
                cipher_key,
                bytes(
                    value,
                    'utf8')),
            'utf-8')

    def run(self, **kwargs):
        """
        confstore_export command execution method.
        It creates a pillar template and loads into the confstore
        of which the path specified in pillar
        """

        try:
            conf = importlib.import_module(
                'cortx.utils.conf_store.conf_store')

            cipher = importlib.import_module('cortx.utils.security.cipher')
        except Exception as exc:
            logger.exception(
                f"Unable to import module due to {exc}")
            raise exc

        try:
            Path(CORTX_CONFIG_DIR).mkdir(parents=True, exist_ok=True)
            template_file_path = str(
                CORTX_CONFIG_DIR /
                'provisioner_confstore_template')
            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name=template_file_path,
                    source='salt://components/system/files/confstore_template.j2',
                    template='jinja'))
            logger.info("Pillar confstore template is created at "
                        f"{template_file_path}"
                        )
        except Exception as exc:
            logger.exception(
                f"Unable to create confstore template due to {exc}")
            raise exc

        try:

            template_data = ""
            with open(template_file_path, 'r') as f:
                template_data = f.read().splitlines()

            if not template_data:
                raise Exception("No content in template file")

            pillar_confstore_path = "provisioner/common_config/confstore_url"
            pillar_key = PillarKey(pillar_confstore_path)
            pillar = PillarResolver(local_minion_id()).get([pillar_key])
            pillar = next(iter(pillar.values()))

            Path(CORTX_CONFIG_DIR).mkdir(parents=True, exist_ok=True)

            conf.Conf.load('provisioner', pillar[PillarKey(pillar_key)])

            for data in template_data:
                if data:
                    key, value = data.split(self.kv_delimiter)
                    if 'secret' in key:
                        value = self._confstore_encrypt(key, value, cipher)
                    conf.Conf.set("provisioner", key, value)

            conf.Conf.save("provisioner")

            logger.info("Template loaded to confstore")

            confstor_path = pillar[PillarKey(pillar_key)].split(':/')[1]

            dest = copy_to_file_roots(confstor_path, CONFSTORE_ROOT_FILE)
            logger.debug("Copied confstore file to salt root directory")

            StateFunExecuter.execute(
                'file.managed',
                fun_kwargs=dict(
                    name=confstor_path,
                    source=str(dest),
                    makedirs=True
                ),
                targets=ALL_MINIONS
            )
            logger.info("Confstore copied across all nodes of cluster")

        except Exception as exc:
            logger.exception(f"Unable to load template due to {exc}")
            raise exc
