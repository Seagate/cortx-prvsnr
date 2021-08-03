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

from provisioner.salt import local_minion_id, function_run
from provisioner.commands import reset_machine_id
from cortx.utils.security.cipher import Cipher
from provisioner.pillar import (
    PillarResolver,
    PillarKey
)


def get_pillar_data(key: str):
    """
    Get pillar_value for the specific key provided

    Parameters
    ----------
    key: str
        keypath for which value to be fetched.
        'key1/key2/key3'

    """
    pillar_key = PillarKey(key)
    pillar = PillarResolver(local_minion_id(), local=True).get([pillar_key])
    pillar = next(iter(pillar.values()))
    return pillar[PillarKey(key)]


def get_machine_id(node: str):
    """
    Get Machine_ID for the specific node

    Parameters
    ----------
    node: str
        minion_id for the node

    """
    machine_id = function_run('grains.get', fun_args=['machine_id'],
                                targets=node)[f'{node}']
    if not machine_id:
        try:
            reset_machine_id.ResetMachineId().run()
            get_machine_id(node)
        except Exception as ex:
            raise ex

    return machine_id


def get_cluster_id():
    """
    Get Cluster_id

    """
    cluster_id = list(function_run('grains.get', fun_args=['cluster_id']).values())[0]

    if not cluster_id:
        raise ValueError("cluster_id not set or missing")

    return cluster_id


def get_enclosure_id(node: str):
    """
    Get Enclosure_ID for the specific node

    Parameters
    ----------
    node: str
        minion_id for the node

    """
    enclosure_id = function_run('grains.get', fun_args=['enclosure_id'],
                                targets=node)[f'{node}']
    if not enclosure_id:
        raise ValueError("enclosure_id is not set or missing")

    return enclosure_id


def get_provisioner_states():
    """
    Get provisioner states system and 3rd party

    """
    return get_pillar_data('execution/noncortx_components')


def get_cortx_states():
    """
    Get cortx states iopath controlpath and system states

    """
    return get_pillar_data('execution/cortx_components')

def get_reset_states():
    """
    Get cortx states iopath controlpath and system states

    """
    return get_pillar_data('reset/cortx_components')

def encrypt_secret(secret, component, key):
    key_cipher = Cipher.generate_key(key, component)
    return Cipher.encrypt(key_cipher, secret.encode("utf-8")).decode("utf-8")

