#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

# Log rotate teardown start
# logrotate.d
# Remove logrotate directory:
#   file.absent:
#     - name: /etc/logrotate.d

# # general settings
# Remove generic logrotate config:
#   file.absent:
#     - name: /etc/logrotate.conf
#     - source: salt://components/system/files/etc/logrotate.conf

# Remove logrotate
# Remove logrotate package:
#   pkg.purged:
#     - name: logrotate

Delete logrotate checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.logrotate
