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

# Service to autoatically perform post-reboot update operations
configure update-post-boot:
  file.managed:
    - name: /etc/systemd/system/update-post-boot.service
    - source: salt://update_post_boot/files/update-post-boot.service
    - mode: 664

Reload service units post adding update-post-boot:
  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - file: configure update-post-boot
  
Enable update-post-boot.service:
  service.enabled:
    - name: update-post-boot.service
