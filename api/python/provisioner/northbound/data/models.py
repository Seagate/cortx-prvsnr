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
#
from provisioner.vendor import attr
from cortx.utils.conf_store import Conf
from .mapping import key_mapping
from provisioner.inputs import (
    NodeParams, NetworkParams
)
from typing import List


class Utils:

    @staticmethod
    def load_conf_store(obj, params):
        if params.get('config_file'):
            config_file = params.pop('config_file')

            try:
                Conf.load(obj.__class__, config_file)
            except Exception as exc:
                if 'already exists' not in str(exc):
                    raise

            for param, value in params.items():
                value = Conf.get(obj.__class__,
                                 key_mapping[param]['confstore_key'])
                setattr(obj, param, value)


@attr.s(auto_attribs=True)
class HostnameModel:
    Hostname: str = NodeParams.hostname
    config_file: str = attr.ib(init=True, default=None)

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        Utils.load_conf_store(self, params)


@attr.s(auto_attribs=True)
class MgmtVipModel:
    Management_VIP: str = NetworkParams.mgmt_vip
    config_file: str = attr.ib(init=True, default=None)

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        Utils.load_conf_store(self, params)


@attr.s(auto_attribs=True)
class TimeServerModel:
    Time_Server: str = attr.ib(init=True,
                               default='time.seagate.com')
    Time_Zone: str = attr.ib(init=True, default='UTC')
    config_file: str = attr.ib(init=True, default=None)

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        Utils.load_conf_store(self, params)


@attr.s(auto_attribs=True)
class MgmtNetworkModel:
    Interfaces_Mgmt: List = NodeParams.mgmt_interfaces
    Ip_Mgmt: List = NodeParams.mgmt_public_ip
    Gateway_Mgmt: List = NodeParams.mgmt_gateway
    Netmask_Mgmt: List = NodeParams.mgmt_netmask

    def __attrs_post_init__(self):
        params = attr.asdict(self)
        Utils.load_conf_store(self, params)
