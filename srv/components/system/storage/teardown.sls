# Setup SWAP and /var/mero
include:
  - components.system.storage.multipath.teardown

{% set node = grains['id'] %}
Unmount metadata vol:
  mount.unmounted:
    - name: /var/mero
    - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2
    - config: /etc/fstab
    - persist: True

Unmount SWAP:
  cmd.run:
    - name: swapoff -a

Remove swap:
  module.run:
    - mount.rm_fstab:
      - name: SWAP
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
  
Remove partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1
