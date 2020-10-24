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

# Custom User Messages for CHECK / ERROR/ LOG
# are listed here. These can be standardised any time.

# Pre-Factory Deployment: Log messages
MLNX_INSTALL_CHECK = "mlnx_ofed_installed CHECK: Mellanox OFED Is Installed"
MLNX_INSTALL_ERROR = "mlnx_ofed_installed ERROR: Mellanox OFED Is Not Installed"
MLNX_HCA_CHECK = "mlnx_hca_present CHECK: Mellanox HCA Present"
MLNX_HCA_ERROR = "mlnx_hca_present ERROR: Mellanox HCA Not Present"
MLNX_HCA_PORTS_CHECK = "mlnx_hca_req_ports CHECK: Mellanox HCA Present And Has Required Number Of Ports"
MLNX_HCA_PORTS_ERROR = "mlnx_hca_req_ports ERROR: Mellanox HCA Present But Does Not Have Required Number Of Ports"
LSB_HBA_PORTS_CHECK = "lsb_hba_req_ports CHECK: LSB HBA Present And Has Required Number Of Ports"
LSB_HBA_PORTS_ERROR = "lsb_hba_req_ports ERROR: LSB HBA Present But Does Not Have Required Number of ports"
LSB_HBA_CHECK = "lsb_hba_present CHECK: LSB HBA Present"
LSB_HBA_ERROR = "lsb_hba_present ERROR: LSB HBA Not Present"
VOLUMES_ACCESSIBLE_CHECK = "volumes_accessible CHECK: Enclosure Volumes Are Accessible From Both Servers"
VOLUMES_ACCESSIBLE_ERROR = "volumes_accessible ERROR: Enclosure Volumes Are Not Accessible"
VOLUMES_MAPPED_TO_CNTRLRS_CHECK = "volumes_mapped CHECK: Enclosure Volumes Are Mapped To Both Controllers"
VOLUMES_MAPPED_TO_CNTRLRS_ERROR = "volumes_mapped ERROR: Enclosure Volumes Not Mapped to Controllers. Run rescan_scsi_bus.sh file"

# BMC Accessible
BMC_ACCESSIBLE_CHECK = "check_bmc_accessible CHECK: BMC Is Accessible On Both Servers"
BMC_ACCESSIBLE_ERROR = "check_bmc_accessible ERROR: BMC Is Inaccessible On Servers. Please Check."
PING_BMC_IP_CHECK = "ping_bmc CHECK: BMC IP Ping Success"
PING_BMC_IP_ERROR = "ping_bmc ERROR: BMC IP Not Reachable"
BMC_IP_ERROR = "ping_bmc ERROR: Failed to get BMC IP."

# Nodes Status
NODES_ONLINE = "nodes_status CHECK: All Nodes Active and Online"
NODES_OFFLINE = "nodes_status ERROR: One or more Nodes Inctive and Offline"
PILLAR_DATA_CHECK = "get_pillar CHECK: Pillar Config Data Obtained"
PILLAR_DATA_ERROR = "get_pillar ERROR: Pillar Config Data Error"
RESOURCE_FAIL_CHECK = "get_resource_failcount CHECK: No Resource Failure Seen. All OK"
RESOURCE_FAIL_ERROR = "get_resource_failcount ERROR: One or More Resources Seemed To Have Failed. Please Check."
CLUSTER_HEALTH_CHECK = "cluster_status CHECK: Nodes In The Cluster Are Healthy."
CLUSTER_HEALTH_ERROR = "cluster_status ERROR: One or More Nodes In The Cluster Not Online. Please Check."

# Post-Factory Deployment: Pacemaker messages
PACEMAKER_HEALTH_CHECK = "corosync_status CHECK: Pacemaker Health Check OK"
PACEMAKER_HEALTH_ERROR = "corosync_status ERROR: Pacemaker Health Check Not OK"
STONITH_CHECK = "stonith_issues CHECK: No STONITH Issues Seen"
STONITH_ERROR = "stonith_issues ERROR: STONITH Issues Seen. Please Check Logs"
CTRL_IP_ACCESSIBLE_ERROR = "check_controller_mc_accessible ERROR: IP Not Reachable. Please Check"

# Post-Factory Deployment: Cortx Check messages
CONSUL_SERVICE_CHECK = "consul_service Consul Service Running"
CONSUL_SERVICE_ERROR = "consul_service Consul Service Not Running"
ES_SERVICE_CHECK = "elasticsearch_service ElasticSearch Running"
ES_SERVICE_ERROR = "elasticsearch_service ElasticSearch Not Running"
IO_SERVICE_CHECK = "ioservice_service IO Services Running"
IO_SERVICE_ERROR = "ioservice_service IO Services Not Running"

# Post-Factory Deployment: Server Check messages
MGMT_VIP_CHECK = "Management VIP is Set in Pillars"
MGMT_VIP_ERROR = "Management VIP is Not Set in Pillars"
CLUSTER_IP_CHECK = "Cluster IP is Set in Pillars"
CLUSTER_IP_ERROR = "Cluster IP is Not Set in Pillars"

# Remote Execution messages
SSH_CONN_ERROR = "ssh_remote_machine ERROR: SSH Conection Failed to Establish"
DECRYPT_PASSWD_CMD_ERROR = "decrypt_secret ERROR: salt-call: command not found"
DECRYPT_PASSWD_FAILED = "decrypt_secret ERROR: Failed to decrypt Secret"
