include:
  - components.nfs.prepare
  - components.nfs.install
  #- components.nfs.config
  - components.nfs.housekeeping
  #- components.sspl.sanity_check

Generate nfs checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.nfs
    - makedirs: True
    - create: True
