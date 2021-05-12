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

upgrade:
  sw_list:
    motr:
      sls: components.motr
      mini: /opt/seagate/cortx/motr/conf/setup.yaml
    s3server:
      sls: components.s3server
      mini: /opt/seagate/cortx/s3/conf/setup.yaml
    hare:
      sls: components.hare
      mini: /opt/seagate/cortx/hare/conf/setup.yaml
    ha:
      sls: components.ha.cortx-ha
      mini: /opt/seagate/cortx/ha/conf/setup.yaml
    sspl:
      sls: components.sspl
      mini: /opt/seagate/cortx/sspl/conf/setup.yaml
    uds:
      sls: components.uds
      mini: /opt/seagate/cortx/uds/conf/setup.yaml
    csm:
      sls: components.csm
      mini: /opt/seagate/cortx/csm/conf/setup.yaml
  yum_snapshots: {} # define specific cortx-version's yum-txn-id for each node
                    # <cortx-version>:
                    #   <node-id>: <yum-txn-id>
