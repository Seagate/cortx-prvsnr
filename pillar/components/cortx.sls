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

cortx:
  software:
    csm:
      user: cortxub
      secret:
    openldap:
      backend_db: mdb
      root:
        user: admin
        secret:
      sgiam:
        user: sgiamadmin
        secret:
    corosync-pacemaker:
      cluster_name: cortx_cluster
      user: hacluster
      secret:
    kafka:
      version: 2.13-2.7.0
      port: 9092
    zookeeper:
      # Ref: https://docs.confluent.io/platform/current/zookeeper/deployment.html#multi-node-setup
      client_port: 2181
      leaderport_port: 2888
      election_port: 3888
    support:
      user: cortxsupport
      password:
  release:
    product: LR2
    setup: cortx
