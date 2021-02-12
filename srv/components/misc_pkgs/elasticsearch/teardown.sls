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

Remove ES and related pkgs:
  pkg.purged:
    - pkgs:
      - rsyslog-elasticsearch
      - rsyslog-mmjsonparse
      - elasticsearch-oss
      - java-1.8.0-openjdk-headless

Remove elasticsearch config:
  file.absent:
    - name: /etc/elasticsearch

Remove elasticsearch data:
  file.absent:
    - name: /var/lib/elasticsearch

Delete elasticsearch checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.elasticsearch
