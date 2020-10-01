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

Create /var/log/crash directoyr:
  file.directory:
    - name: /var/log/crash
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

Relocate core dump to /var/log/crash:
  sysctl.present:
    - name: kernel.core_pattern
    - value: '|/bin/sh -c $@ -- eval exec gzip --fast > /var/log/crash/core-%e.%p.gz'
    - config: /etc/sysctl.d/200-motr-dumps.conf

Load updated sysctl settings:
  cmd.run:
    - name: sysctl -p /etc/sysctl.d/200-motr-dumps.conf
    - require:
      - Relocate core dump to /var/log/crash

update /etc/kdump.conf:
  file.line:
    - name: /etc/kdump.conf
    - content: "core_collector makedumpfile -c --message-level 1 -d 31"
    - match: "core_collector makedumpfile -l --message-level 1 -d 31"
    - mode: "replace"

cron job for coredumps rotation:
  file.managed:
    - name: /etc/cron.hourly/coredumps_rotate
    - contents: |
        #!/bin/sh
{% if "physical" in grains['virtual'] %}
        ls -t /var/log/crash/core-* | tail -n +60 | xargs rm -f
{% else %}
        ls -t /var/log/crash/core-* | tail -n +6 | xargs rm -f
{% endif %}
        EXITVALUE=$?
        if [ $EXITVALUE != 0 ]; then
            /usr/bin/logger -t coredumps "ALERT coredumps rotation exited abnormally with [$EXITVALUE]"
        fi
        exit 0
    - create: True
    - makedirs: True
    - replace: False
    - user: root
    - group: root
    - dir_mode: 755
    - mode: 0700
