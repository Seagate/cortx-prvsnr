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


# general settings
Logrotate config file - Generic:
  file.managed:
    - name: /etc/logrotate.conf
    {% if "physical" in grains['virtual'] %}
    - source: salt://components/system/logrotate/files/etc/logrotate.conf
    {% else %}
    - source: salt://components/system/logrotate/files/etc/logrotate_vm.conf
    {% endif %}

# logrotate.d
Create logrotate.d with specific component settings:
  file.recurse:
    - name: /etc/logrotate.d
    - source: salt://components/system/logrotate/files/etc/logrotate.d
    - keep_source: True
    - dir_mode: 0750
    - file_mode: 0640
    - user: root
    - group: root
    - clean: False
    - include_empty: True


Create logrotate_setup.d with specific component settings:
  file.recurse:
    - name: /etc/logrotate_setup.d
    {% if "physical" in grains['virtual'] %}
    - source: salt://components/system/logrotate/files/etc/logrotate_hw.d
    {% else %}
    - source: salt://components/system/logrotate/files/etc/logrotate_vm.d
    {% endif %}
    - keep_source: True
    - dir_mode: 0750
    - file_mode: 0640
    - user: root
    - group: root
    - clean: False
    - include_empty: True

# Setup cron job:
#   file.managed:
#     - name: /etc/cron.daily/logrotate
#     - contents: |
#         #!/bin/sh
#         /usr/sbin/logrotate -s /var/lib/logrotate/logrotate.status /etc/logrotate.conf
#         EXITVALUE=$?
#         if [ $EXITVALUE != 0 ]; then
#             /usr/bin/logger -t logrotate "ALERT exited abnormally with [$EXITVALUE]"
#         fi
#         exit 0
#     - create: True
#     - makedirs: True
#     - replace: False
#     - user: root
#     - group: root
#     - dir_mode: 755
#     - mode: 0700

Setup cron job:
  file.managed:
    - name: /etc/cron.hourly/logrotate
    - contents: |
        #!/bin/sh
        /usr/sbin/logrotate -s /var/lib/logrotate/logrotate.status /etc/logrotate.conf
        EXITVALUE=$?
        if [ $EXITVALUE != 0 ]; then
            /usr/bin/logger -t logrotate "ALERT exited abnormally with [$EXITVALUE]"
        fi
        exit 0
    - create: True
    - makedirs: True
    - replace: False
    - user: root
    - group: root
    - dir_mode: 755
    - mode: 0700
