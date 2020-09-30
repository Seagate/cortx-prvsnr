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

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
{% set logfile = "/var/log/seagate/provisioner/sanity_tests.log" %}
Create SSPL Sanity test script:
  file.managed:
      - name: /tmp/sspl-sanity.sh
      - create: True
      - makedirs: True
      - replace: True
      - user: root
      - group: root
      - mode: 755
      - contents: |
          #!/bin/bash
          echo "Runnign SSPL sanity"
          echo "state=active" > /var/cortx/sspl/data/state.txt
          PID=$(/sbin/pidof -s /usr/bin/sspl_ll_d)
            kill -s SIGHUP $PID
          sh /opt/seagate/cortx/sspl/sspl_test/run_tests.sh

Run SSPL Sanity tests:
  cmd.run:
    - name: bash /tmp/sspl-sanity.sh 2>&1 | tee {{ logfile }}
    - require:
      - Create SSPL Sanity test script

Housekeeping:
  file.absent:
    - name: /tmp/sspl-sanity.sh
    - require:
      - Run SSPL Sanity tests

{% endif %}
