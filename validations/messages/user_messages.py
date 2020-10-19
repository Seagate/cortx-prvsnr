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

# Common Messages for CHECK / ERROR/ LOG will be listed here

from enum import Enum
from pathlib import Path
from typing import Union, Dict, Optional

CONFIG_MODULE_DIR = Path(__file__).resolve().parent

# Pre-Factory Deployment: Log messages

MLNX_INSTALL_CHECK = "CHECK: Mellanox OFED Is Installed"
MLNX_INSTALL_ERROR = "ERROR: Mellanox OFED Is Not Installed"
MLNX_HCA_CHECK = "CHECK: Mellanox HCA Present"
MLNX_HCA_ERROR = "ERROR: Mellanox HCA Not Present"
MLNX_HCA_PORTS_CHECK = "CHECK: Mellanox HCA Present And Has Required Number Of Ports"
MLNX_HCA_PORTS_ERROR = "ERROR: Mellanox HCA Present But Does Not Have Required Number Of Ports"
LSB_HBA_PORTS_CHECK = "CHECK: LSB HBA Present And Has Required Number Of Ports"
LSB_HBA_PORTS_ERROR = "ERROR: LSB HBA Present But Does Not Have Required Number of ports"
LSB_HBA_CHECK = "CHECK: LSB HBA Not Present"
LSB_HBA_ERROR = "ERROR: LSB HBA Not Present"
VOLUMES_ACCESSIBLE_CHECK = "CHECK: Enclosure Volumes Are Accessible From Both Servers" 
VOLUMES_ACCESSIBLE_ERROR = "ERROR: Enclosure Volumes Are Not Accessible"
VOLUMES_MAPPED_TO_CNTRLRS_CHECK = "CHECK: Enclosure Volumes Are Mapped To Both Controllers" 
VOLUMES_MAPPED_TO_CNTRLRS_ERROR = "ERROR: Enclosure Volumes Not Mapped to Controllers. Run rescan_scsi_bus.sh file"

# Nodes Status
NODES_ONLINE = "CHECK: All Nodes Active and Online" 
NODES_OFFLINE = "ERROR: One or more Nodes Inctive and Offline"
RESOURCE_FAIL_CHECK = "CHECK: No Resource Failure Seen. All OK"
RESOURCE_FAIL_ERROR = "ERROR: One or More Resources Seemed To Have Failed. Please Check."
CLUSTER_HEALTH_ERROR = "ERROR: One or More Nodes In The Cluster Not Online. Please Check."

# Post-Factory Deployment: Pacemaker messages
PACEMAKER_HEALTH_CHECK = "CHECK: Pacemaker Health Check OK"
PACEMAKER_HEALTH_ERROR = "ERROR: Pacemaker Health Check Not OK"
STONITH_CHECK = "CHECK: No STONITH Issues Seen"
STONITH_ERROR = "ERROR: STONITH Issues Seen. Please Check Logs"

# Post-Factory Deployment: Cortx Check messages
CONSUL_SERVICE_CHECK = "Consul Service Running"
CONSUL_SERVICE_ERROR = "Consul Service Not Running"
ES_SERVICE_CHECK = "ElasticSearch Running"
ES_SERVICE_ERROR = "ElasticSearch Not Running"
IO_SERVICE_CHECK = "IO Services Running"
IO_SERVICE_ERROR = "IO Services Not Running"

# Post-Factory Deployment: Server Check messages
MGMT_VIP_CHECK = "Management VIP is Set in Pillars"
MGMT_VIP_ERROR = "Management VIP is Not Set in Pillars"
CLUSTER_IP_CHECK = "Cluster IP is Set in Pillars"
CLUSTER_IP_ERROR = "Cluster IP is Not Set in Pillars"

