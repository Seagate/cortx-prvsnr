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

{% set server_nodes = [ ] -%}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
{%- if ("primary" in pillar['cluster'][grains['id']]['roles']) and
  (1 < (server_nodes | length))
%}
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
          echo "Running swapoff -a on current node(srvnode-1)"
          timeout -k 10 30 swapoff -a ||true
          echo "Runnign swapoff -a on srvnode-2 node"
          ssh srvnode-2 "timeout -k 10 30 swapoff -a || true"
          echo "Cleaning up partitions"
          for dev in `ls /dev/mapper/mpath* | grep '[1-2]$' | rev | cut -c 2- | rev | sort -u`
          do
            # timeout -k 10 30 parted -s $dev rm 6 || true
            # timeout -k 10 30 parted -s $dev rm 5 || true
            # timeout -k 10 30 parted -s $dev rm 4 || true
            # timeout -k 10 30 parted -s $dev rm 3 || true
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
