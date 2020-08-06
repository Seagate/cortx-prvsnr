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

{% set node_id = grains['id'] %}
{%- if pillar['cluster'][node_id]['is_primary'] %}
Create tidy-up script:
  file.managed:
      - name: /tmp/storage-tidy-up.sh
      - create: True
      - makedirs: True
      - replace: True
      - user: root
      - group: root
      - mode: 755
      - contents: |
          #!/bin/bash
          echo "Runnign swapoff -a on current node(srvnode-1)"
          timeout -k 10 30 swapoff -a ||true
          echo "Runnign swapoff -a on srvnode-2 node"
          ssh srvnode-2 "timeout -k 10 30 swapoff -a || true"
          echo "Cleaning up partitions"
          for dev in `ls /dev/mapper/mpath* | grep '[1-6]$' | rev | cut -c 2- | rev | sort -u`
          do
            timeout -k 10 30 parted -s $dev rm 6 || true
            timeout -k 10 30 parted -s $dev rm 5 || true
            timeout -k 10 30 parted -s $dev rm 4 || true
            timeout -k 10 30 parted -s $dev rm 3 || true
            timeout -k 10 30 parted -s $dev rm 2 || true
            timeout -k 10 30 parted -s $dev rm 1 || true
          done
          echo "Running partprobe on srvnode-1"
          timeout -k 10 30 partprobe || true
          echo "Running partprobe on srvnode-2"
          ssh srvnode-2 "timeout -k 10 30 partprobe || true"
          echo "Running partprobe again on srvnode-1"
          timeout -k 10 30 partprobe || true

Cleanup stale partitions:
  cmd.run:
    - name: bash /tmp/storage-tidy-up.sh || true

Housekeeping:
  file.absent:
      - name: /tmp/storage-tidy-up.sh
{% endif %}
