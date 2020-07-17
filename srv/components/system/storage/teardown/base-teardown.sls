# Setup SWAP and /var/mero
{% set node = grains['id'] %}

{% if "physical" in grains['virtual'] %}
# Steps:
#  - unmount SWAP
#  - remove SWAP from fstab
#  - unmount /var/motr
#  - remove /var/motr partition
#  - delete SWAP and raw_metadata LVs
#  - delete vg_metadata
#  - delete pv_metadata
#  - delete LVM partition
Unmount SWAP:
  module.run:
    - mount.swapoff:
      - name: /dev/vg_metadata/lv_main_swap

Remove swap from fstab:
  module.run:
    - mount.rm_fstab:
      - name: none
      - device: /dev/vg_metadata/lv_main_swap

Unmount /var/mero partition:
  mount.unmounted:
    - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1

Remove /var/mero partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1

Remove LV raw_metadata:
  module.run:
    - lvm.lvremove: 
      - lvname: lv_raw_metadata
      - vgname: vg_metadata
      - force: True

Remove LV swap:
  module.run:
    -lvm.lvremove:
      - lvname: lv_main_swap
      - vgname: vg_metadata
      - force: True

Remove VG:
  module.run:
    - lvm.vgremove:
      - vgname: vg_metadata
      - force: True

Remove PV:
  module.run:
    - lvm.pvremove:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2

Remove LVM partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2
# done with the sequence (h/w)

{% else %}
Unmount SWAP:
  module.run:
    - mount.swapoff:
      - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1

Remove swap from fstab:
  module.run:
    - mount.rm_fstab:
      - name: none
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    # - onlyif: grep {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1 /etc/fstab

Remove swap partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1

Unmount /var/mero partition:
  mount.unmounted:
    - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2

Remove /var/mero partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2
{% endif %}

Refresh partition:
  module.run:
    - partition.probe: []
