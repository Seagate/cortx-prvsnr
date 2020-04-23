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
          echo "Runnign swapoff -a on current node(eosnode-1)"
          timeout -k 10 30 swapoff -a ||true
          echo "Runnign swapoff -a on eosnode-2 node"
          ssh eosnode-2 "timeout -k 10 30 swapoff -a || true"
          echo "Cleaning up partitions"
          for dev in `ls /dev/mapper/mpath* | grep '[1-2]$' | rev | cut -c 2- | rev | sort -u`
          do
            timeout -k 10 30 parted -s $dev rm 2 || true
            timeout -k 10 30 parted -s $dev rm 1 || true
          done
          echo "Running partprobe on eosnode-1"
          timeout -k 10 30 partprobe || true
          echo "Running partprobe on eosnode-2"
          ssh eosnode-2 "timeout -k 10 30 partprobe || true"
          echo "Running partprobe again on eosnode-1"
          timeout -k 10 30 partprobe || true

Cleanup stale partitions:
  cmd.run:
    - name: bash /tmp/storage-tidy-up.sh || true

Housekeeping:
  file.absent:
      - name: /tmp/storage-tidy-up.sh
{% endif %}
