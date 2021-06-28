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

execution:
  noncortx_components:
    platform:
      - system
      - system.storage
      - misc_pkgs.rsyslog
      - system.logrotate
    3rd_party:
      - misc_pkgs.sos
      - misc_pkgs.ipmi.bmc_watchdog
      - misc_pkgs.ssl_certs
      - ha.haproxy
      - misc_pkgs.openldap
      - misc_pkgs.nodejs
      - misc_pkgs.kafka
      - misc_pkgs.elasticsearch
      - misc_pkgs.kibana
      - misc_pkgs.statsd
      - misc_pkgs.consul.install
      - misc_pkgs.lustre
      - misc_pkgs.consul.install
      - ha.corosync-pacemaker.install
      - ha.corosync-pacemaker.config.base
  cortx_components:
    foundation:
      - cortx_utils
    iopath:
      - motr
      - s3server
      - hare
    controlpath:
      - sspl
      - uds
      - csm
    ha:
      - ha.cortx-ha

