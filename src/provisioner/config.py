# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import errno
from cortx.provisioner.error import CortxProvisionerError
from cortx.utils.validator.error import VError

class CortxConfig:
    """ CORTX Configuration """

    def __init__(self, cortx_config: list = []):
        """ Create CORTX config """

        self._cortx_config = cortx_config
        CortxConfig._validate(self._cortx_config)

    @staticmethod
    def _validate(cortx_conf: dict):
        """
        validates a give node to have required properties
        Raises exception if there is any entry missing
        """
        required_keys_for_cortx_conf = [
            'external', 'common']

        for k in required_keys_for_cortx_conf:
            if cortx_conf.get(k) is None:
                raise VError(
                    errno.EINVAL, f"'{k}' property is unspecified in cortx_config.")

            if k == 'external':
                required_external_keys = ['kafka', 'openldap', 'consul']
                for e_key in required_external_keys:
                    try:
                        if cortx_conf[k][e_key]['endpoints'] is None:
                            raise VError(errno.EINVAL,
                                f"'Endpoint for {e_key}' is unspecified in cortx_config.")
                    except KeyError as e:
                        raise CortxProvisionerError(
                            errno.EINVAL,
                            f'{str(e)} is unspecified for external in cortx_config.')

    def save(self, config_store):
        """ Save cortx-config into confstore """

        kvs = []
        try:
            # Update configmap keys as per confstore keys.
            self._cortx_config['common']['setup_type'] = self._cortx_config['common'].pop(
                'environment_type')
            key_prefix = 'cortx>'
            for attr in self._cortx_config.keys():
                kv = (key_prefix + attr, self._cortx_config[attr])
                kvs.append(kv)
            config_store.set_kvs(kvs)
        except KeyError as e:
            raise CortxProvisionerError(
                errno.EINVAL,
                f'Error occurred while adding CORTX config information into confstore {e}')
