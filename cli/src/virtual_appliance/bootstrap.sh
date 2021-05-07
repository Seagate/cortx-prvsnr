#!/bin/sh
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


set -euE

export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/va_bootstrap.log}"
mkdir -p $(dirname "${LOG_FILE}")

function trap_handler {
    echo "***** ERROR! *****"
    echo "For detailed error logs, please see: $LOG_FILE"
    echo "******************"
}
trap trap_handler ERR

BASEDIR=$(dirname "${BASH_SOURCE}")

#reconfigure pillar
provisioner configure_setup ~/config.ini 1
provisioner confstore_export

#reconfigure network
salt-call state.apply components.system.network
salt-call state.apply components.system.network.mgmt.public
salt-call state.apply components.system.network.data.public
salt-call state.apply components.system.network.data.direct

salt-call state.apply components.system.config.sync_salt

#reconfigure /etc/hosts
salt-call state.apply components.system.config.hosts

#reconfigure firewall
salt-call state.apply components.system.firewall.teardown
salt-call state.apply components.system.firewall

#reconfigure kafka
salt-call state.apply components.misc_pkgs.kafka.config
salt-call state.apply components.misc_pkgs.kafka.start
salt-call state.apply components.misc_pkgs.kafka.sanity_check
salt-call state.apply components.cortx_utils.config
salt-call state.apply components.cortx_utils.sanity_check

#reconfigure lustre
salt-call state.apply components.misc_pkgs.lustre.stop
salt-call state.apply components.misc_pkgs.lustre.config

echo "INFO: Restarting rabbitmq-server" | tee -a "${LOG_FILE}"
systemctl restart rabbitmq-server
echo "INFO: Restarting elasticsearch" | tee -a "${LOG_FILE}"
systemctl restart elasticsearch


#configure s3server
echo "INFO: Configuring haproxy and s3" | tee -a "${LOG_FILE}"
salt "*" state.apply components.s3server.config | tee -a "${LOG_FILE}"
salt "*" state.apply components.s3server.start | tee -a "${LOG_FILE}"

echo "INFO: Configuring s3 ips in /etc/hosts" | tee -a "${LOG_FILE}"
DATA_IF=$(salt-call pillar.get cluster:srvnode-1:network:data:public_interfaces:0 --output=newline_values_only)
DATA_IP=$(salt-call grains.get ip4_interfaces:${DATA_IF}:0 --output=newline_values_only)
provisioner pillar_set s3clients/s3server/ip \"${DATA_IP}\"
salt "*" state.apply components.s3clients.config | tee -a "${LOG_FILE}"

#reconfigure hare CDF
salt-call state.apply components.hare.config

#configure and start sspl
echo "INFO: Configuring sspl" | tee -a "${LOG_FILE}"
salt "*" state.apply components.sspl.config | tee -a "${LOG_FILE}"
salt "*" state.apply components.sspl.start | tee -a "${LOG_FILE}"

#start csm services
echo "INFO: Restarting csm services" | tee -a "${LOG_FILE}"
salt "*" state.apply components.csm.config | tee -a "${LOG_FILE}"
salt "*" state.apply components.csm.start | tee -a "${LOG_FILE}"

#bootstrap cluster
echo "INFO: Bootstraping cluster" | tee -a "${LOG_FILE}"
cortx cluster start | tee -a "${LOG_FILE}"
hctl status | tee -a "${LOG_FILE}"

echo "Done ! " | tee -a "${LOG_FILE}"
