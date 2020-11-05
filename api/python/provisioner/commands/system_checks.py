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
import logging
from typing import Type
from . import CommandParserFillerMixin
from .. import inputs
from .. import config
from ..vendor import attr


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class SystemChecksArgs:
    check_name: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "name of check/validation alias",
                'choices': config.SYSTEM_CHECKS
            }
        }
    )


@attr.s(auto_attribs=True)
class SystemChecks(CommandParserFillerMixin):
    """
    Class for all checks,pre and post deployement, node_replacement,
    unboxing, fw update etc
    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = SystemChecksArgs

    def _imports(self):
        """
        Imports all checks from utils
        """
        from cortx.utils.kvstore.pillar import PillarStorage
        from cortx.utils.validator.v_storage import StorageV
        from cortx.utils.validator.v_network import NetworkV
        from cortx.utils.validator.v_salt import SaltV

        self._pillar = PillarStorage()
        self._storage = StorageV()
        self._network = NetworkV()
        self._salt = SaltV()

    def _all_nodes_cluster_data(self, key):
        nodes = self._pillar.get("cluster:node_list")
        res = []
        for node in nodes:
            resp = self._pillar.get(f"cluster:{node}:{key}")
            res.append(resp)
        return res

    def _network_checks(self):
        """Network related checks."""
        logger.info("Validating mgmt vip")
        mgmt_vip = self._pillar.get("cluster:mgmt_vip")
        self._network.validate('connectivity', mgmt_vip)

        logger.info("Validating cluster ip")
        cluster_ip = self._pillar.get("cluster:cluster_ip")
        self._network.validate('connectivity', cluster_ip)

        logger.info("Validating public data ips")
        pub_ips = self._all_nodes_cluster_data(
                  "network:data_nw:public_ip_addr")
        self._network.validate('connectivity', pub_ips)

        logger.info("Validating private data ips")
        pvt_ips = self._all_nodes_cluster_data("network:data_nw:pvt_ip_addr")
        self._network.validate('connectivity', pvt_ips)

    def _post_checks(self):
        """Run all post deployment checks."""

        nodes = self._pillar.get("cluster:node_list")

        logger.info("Validating passwordless ssh")
        args = ['root']
        args.extend(nodes)
        self._network.validate('passwordless', args)

        logger.info("Validating salt minion connectivity")
        self._salt.validate('minions', nodes)

        logger.info("Validating network checks")
        self._network_checks()

        logger.info("Validating storage lvms")
        self._storage.validate('lvms', nodes)

        logger.info("Validating storage luns")
        self._storage.validate('luns', nodes)

    def run(self, check_name):
        """
        Run all system checks

        :param str check_name: name of check to run
        :return:
        """
        self._imports()
        try:
            res = getattr(self,
                          f"_{check_name}")()
        except AttributeError:
            raise ValueError(f'Check "{check_name}" is not implemented')

        return res
