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
  - .install
  - .start


Update HW clock sync:
  file.managed:
    - name: /etc/sysconfig/ntpdate
    - source: salt://components/system/ntp/files/ntpdate.conf
    - makedirs: True
    - keep_source: True
    - require:
      - ntp_package
    - watch_in:
      - ntp_service

Setup NTP config file:
  file.managed:
    - name: /etc/ntp.conf
    - source: salt://components/system/ntp/files/ntp.conf
    - makedirs: True
    - keep_source: True
    - template: jinja
    - require: 
      - ntp_package
    - watch_in:
      - ntp_service

Setup time zone:
  timezone.system:
    - name: {{ pillar['system']['ntp']['timezone'] }}
    - require:
      - Setup NTP config file
    - watch_in:
      - ntp_service
