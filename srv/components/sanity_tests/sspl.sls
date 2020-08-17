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
