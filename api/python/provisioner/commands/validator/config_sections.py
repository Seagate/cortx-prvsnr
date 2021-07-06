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
# Validation module for config file


import logging
from provisioner.vendor import attr
from provisioner.salt import cmd_run,local_minion_id
from provisioner.config import ALL_MINIONS
from provisioner.api import grains_get
import psutil

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ConfigValidator:

    def _parse_sections(self, content):  # noqa: C901
        """Parses the content of config file."""
        output = {}
        servers = {}
        enclosures = {}

        for section, data in content.items():
            if 'srvnode' in section:
                if 'default' in section:
                    output["srvnode_default"] = data
                else:
                    servers[section] = data

            elif 'enclosure' in section:
                if 'default' in section:
                    output["enclosure_default"] = data
                else:
                    enclosures[section] = data

            elif 'cluster' in section:
                output["cluster"] = data

        output["node"] = servers
        output["enclosure"] = enclosures

        logger.debug(f"Parsed config output: {output}")

        return output

    def _validate_node_count(self, num_of_nodes, parsed):  # noqa: C901
        """
        Validates number of nodes.

        Node count can only be 1 or multiples of 3.
        There cannot be mismatch between count of
        node sections and enclosure sections.
        """
        try:
            logger.info(
               f"Validating data for {num_of_nodes}-node(s) setup"
            )

            if not (int(num_of_nodes) == 1 or int(num_of_nodes) % 3 == 0):
                raise ValueError(
                  f"{num_of_nodes} nodes provided. "
                  "Setup configuration can be done only on single node or "
                  "in a cluster of node count in 3s"
                )
            else:
                if ("srvnode_default" and not "enclosure_default" in parsed or
                   "enclosure_default" and not "srvnode_default" in parsed):

                    raise ValueError(
                      "Default sections for servers and enclosures must be unianimous. "
                      "Either both 'srvnode_default' and 'enclosure_default' sections "
                      "must be present together or not."
                    )

                node_count = len(parsed["node"])

                enclosure_count = len(parsed["enclosure"])

                if node_count != int(num_of_nodes):
                    raise ValueError(
                      f"Node count mismatch! '{int(num_of_nodes)}' is given in input "
                      f"whereas, data for '{node_count}'-node(s) is given in config file."
                    )

                elif not (node_count == 1 or node_count % 3 == 0):
                    raise ValueError(
                      f"Data for {node_count} nodes provided in config. "
                      "Setup configuration can be done only on single node or "
                      "in a cluster of node count in 3s"
                    )

                elif enclosure_count != node_count:
                    logger.error(
                        "ERROR: Invalid config data encountered. Count of node sections "
                        "and enclosure sections in config file do not match."
                    )
                    raise ValueError(
                       f"Number of enclosure sections: '{enclosure_count}' "
                       f"does not match with number of node sections: '{node_count}'"
                    )

                else:
                    logger.info(
                        "Success: Node Validation done. "
                        f"Applying config for {node_count}-node setup"
                    )

        except Exception as exc:
            raise ValueError(f"Config Failed to apply: {str(exc)}")

    def _validate_null_values(self,config):
        try:
            for section in config.sections():
                for option in config.options(section):
                    if not config.get(section, option):
                        raise ValueError(
                            f"'{option}' has no value passed in config.ini under section : '{section}' "
                        )
        except Exception as exc:
            raise ValueError(f"Config Failed to apply: {str(exc)}")

    def _validate_config_interfaces(self,config):
        try:
            for section in config.sections() :
                if ("srvnode" in section):
                    if (config.has_option(section,'network.data.private_interfaces')):
                        machine_interface = psutil.net_if_addrs()
                        user_interfaces = config[section]['network.data.private_interfaces'].split(",")
                        user_interfaces.extend(config[section]['network.data.public_interfaces'].split(","))
                        user_interfaces.extend(config[section]['network.mgmt.interfaces'].split(","))
                        if (set(interface in machine_interface for interface in user_interfaces) == set([True])) :
                            logger.debug(
                                "Success: Interfaces Validation done. "
                            )
                        else :
                            raise ValueError(
                                f"incorrect interfaces passed in config.ini under section : '{section}' "
                            )
        except Exception as exc:
            raise ValueError(f"Config Failed to apply: {str(exc)}")

    def _validate_config_devices(self,config) :
        try :
            for section in config.sections() :
                if ("srvnode" in section):
                    if (config.has_option(section,'storage.cvg.0.data_devices')):
                        devices = config[section]['storage.cvg.0.data_devices'].split(",")
                        devices.extend(config[section]['storage.cvg.0.metadata_devices'].split(","))
                        for device in devices:
                            if 'default' in section:
                                target= ALL_MINIONS
                            else:
                                target= local_minion_id()
                            cmd_run(f"ls {device}", targets=target)
        except Exception as exc:
            raise ValueError(f"Config Failed to apply: {str(exc)}")
