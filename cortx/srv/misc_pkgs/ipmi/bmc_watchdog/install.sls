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

Install bmc-watchdog:
  pkg.installed:
    - name: freeipmi-bmc-watchdog

Update watchdog timeout:
  file.replace:
    - name: /etc/sysconfig/bmc-watchdog
    - pattern: '-i 900'
    - repl: '-i 300'

Reload kernel for bmc-watchdog:
  file.managed:
    - name: /etc/modules-load.d/ipmi_mods.conf
    - contents: |
        # Load at boot:
        ipmi_devintf
        ipmi_si
        ipmi_msghandler
    - create: True
    - makedirs: True
    - replace: True
    - user: root
    - group: root
    - mode: 644
    - dir_mode: 755
