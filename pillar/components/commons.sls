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

commons:
  health-map:
    path: /opt/seagate/cortx_configs/healthmap/
    file: healthmap-schema.json
  version:
    consul: 1.7.8-1
    # elasticsearch: 6.8.8-1
    elasticsearch-oss: 6.8.8-1
    erlang: latest
    kibana-oss: 6.8.8-1
    nodejs: v12.13.0
    rabbitmq: latest
    rsyslog: 8.40.0-1.el7
    rsyslog-elasticsearch: 8.40.0-1.el7
    rsyslog-mmjsonparse: 8.40.0-1.el7
    cortx-s3server: latest
    cortx-s3iamcli: latest
    kafka: 2.13-2.7.0
