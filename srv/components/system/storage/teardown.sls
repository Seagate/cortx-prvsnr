# Setup SWAP and /var/mero
{% set node = grains['id'] %}

Unmount SWAP:
  cmd.run:
    - name: swapoff {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1

Remove swap:
  module.run:
    - mount.rm_fstab:
      - name: none
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1

Delete swap partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2

Delete /var/mero partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1

Delete storage checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.storage
