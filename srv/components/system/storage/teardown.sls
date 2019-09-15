# Setup SWAP and /var/mero
{% set node = grains['id'] %}

Stop and disable multipath service:
  service.dead:
    - name: multipathd.service

Remove multipath service:
  pkg.purged:
    - name: device-mapper-multipath

Remove multipath config:
  file.absent:
    - name: /etc/multipath.conf

Unmount metadata vol:
  mount.unmounted:
    - name: /var/mero
    - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part2
    - config: /etc/fstab
    - persist: True

Unmount swap:
  module.run:
    - mount.swapoff:
      - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part1
    - mount.rm_fstab:
      - name: SWAP
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}-part1
  
Remove partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1
