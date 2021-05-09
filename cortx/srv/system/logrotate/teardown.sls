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

Remove logrotate package:
  pkg.purged:
    - name: logrotate

Remove generic logrotate config:
  file.absent:
    - name: /etc/logrotate.conf

Remove logrotate directory:
  file.absent:
    - name: /etc/logrotate.d

Remove logrotate setup directory:
  file.absent:
    - name: /etc/logrotate_setup.d

#Remove logrotate cron.daily:
#  file.absent:
#    - name: /etc/cron.daily/logrotate

Remove logrotate cron.hourly:
  file.absent:
    - name: /etc/cron.hourly/logrotate

Delete logrotate checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.logrotate
