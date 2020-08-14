{%- if (pillar['cluster'][grains['id']]['is_primary']) and (1 < pillar['cluster']['node_list'] | length) %}
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
