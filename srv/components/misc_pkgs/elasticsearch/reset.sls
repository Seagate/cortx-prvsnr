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

include:
  - components.misc_pkgs.elasticsearch.stop
    
Remove elasticsearch package:
  cmd.run:
    - name: "rpm -e --nodeps rsyslog-elasticsearch rsyslog-mmjsonparse opendistroforelasticsearch elasticsearch-oss opendistro-sql"

Remove opendistro package:
  cmd.run:
    - name: "rpm -e --nodeps opendistro-alerting opendistro-anomaly-detection opendistro-index-management opendistro-job-scheduler opendistro-knn opendistro-knnlib opendistro-performance-analyzer opendistro-reports-scheduler opendistro-security "

Remove elasticsearch config:
  file.absent:
    - name: /etc/elasticsearch

Remove elasticsearch data:
  file.absent:
    - name: /var/lib/elasticsearch

Remove elasticsearch logs:
  file.absent:
    - name: /var/log/elasticsearch

Delete elasticsearch checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.elasticsearch
