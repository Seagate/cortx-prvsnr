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

base:
  '*':
    - components.system
    - components.system.storage
    # Dependecies
    - components.misc_pkgs.rsyslog
    - components.ha.corosync-pacemaker
    - components.ha.haproxy
    - components.misc_pkgs.elasticsearch
    - components.misc_pkgs.kibana
    - components.misc_pkgs.nodejs
    - components.misc_pkgs.openldap
    - components.misc_pkgs.rabbitmq
    - components.misc_pkgs.statsd
    - components.misc_pkgs.ssl_certs
    # IO Stack
    - components.misc_pkgs.lustre
    - components.motr
    - components.s3server
    - components.hare
    # Management Stack
    - components.sspl
    - components.uds
    - components.csm
