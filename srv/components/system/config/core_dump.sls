#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

Relocate core dump to /var/crash:
  sysctl.present:
    - name: kernel.core_pattern
    - value: '|/bin/sh -c $@ -- eval exec gzip --fast > /var/crash/core-%e.%p.gz'
    - config: /etc/sysctl.d/200-motr-dumps.conf

Load updated sysctl settings:
  cmd.run:
    - name: sysctl -p /etc/sysctl.d/200-motr-dumps.conf
    - require:
      - Relocate core dump to /var/crash

update /etc/kdump.conf:
  file.line:
    - name: /etc/kdump.conf
    - content: "core_collector makedumpfile -c --message-level 1 -d 31"
    - match: "core_collector makedumpfile -l --message-level 1 -d 31"
    - mode: "replace"

cron job for coredumps rotation:
  file.managed:
    - name: /etc/cron.daily/coredumps_rotate
    - contents: |
        #!/bin/sh
        ls -t /var/crash/core-* | tail -n +60 | xargs rm -f
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
