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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

commons:
  cortx_commons:
    # includes different 3rd party artifacts
    # (multiple rpm repositories, raw archives, bash scirpts etc.)
    RedHat: http://cortx-storage.colo.seagate.com/releases/cortx/uploads/rhel/rhel-7.7.1908/
    CentOS: http://cortx-storage.colo.seagate.com/releases/cortx/uploads/centos/centos-7.7.1908/
  version:
    # elasticsearch: 6.8.8-1
    elasticsearch-oss: 6.8.8-1
    erlang: latest
    kibana-oss: 6.8.8-1
    nodejs: v12.13.0
    rabbitmq: latest
    rsyslog: 8.40.0-1.el7
    rsyslog-elasticsearch: 8.40.0-1.el7
    rsyslog-mmjsonparse: 8.40.0-1.el7
  repo:
    # base urls for lustre yum repositories (one per different networks: tcp, o2ib)
    # TODO IMPROVE EOS-12508 remove, should be related to cortx_common
    lustre: http://cortx-storage.colo.seagate.com/releases/cortx/lustre/custom/
