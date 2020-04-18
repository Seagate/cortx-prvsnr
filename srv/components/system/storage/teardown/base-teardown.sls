# Setup SWAP and /var/mero
{% set node = grains['id'] %}

Unmount SWAP:
  cmd.run:
    - name: swapoff {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1 ||true

Remove swap:
  module.run:
    - mount.rm_fstab:
      - name: none
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    - onlyif: grep {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1 /etc/fstab

Delete swap partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2
    - onlyif: lsblk | grep `echo {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2 | cut -d/ -f5 | cut -d- -f3`

Delete /var/mero partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1
    - onlyif: lsblk | grep `echo {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1 | cut -d/ -f5 | cut -d- -f3`

Refresh partition:
  module.run:
    - partition.probe: []

