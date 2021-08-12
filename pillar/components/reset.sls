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

reset:
  cortx_components:
    ha:
      - ha.cortx-ha
    controlpath:
      - uds
      - csm
      - sspl
    iopath:
      - hare
      - s3server
      - motr
    foundation:
      - cortx_utils
  non_cortx_components:
    3rd party:
      - ha.corosync-pacemaker
      - misc_pkgs.kafka
      - misc_pkgs.lustre
      - misc_pkgs.statsd
      - misc_pkgs.kibana
      - misc_pkgs.elasticsearch
      - misc_pkgs.nodejs
      - misc_pkgs.consul
      - misc_pkgs.openldap
      - ha.haproxy
  system_components:
    system:
      - system.chrony
      - system.logrotate
      - system.firewall
      - misc_pkgs.rsyslog
      - system.storage
      - system.storage.multipath
