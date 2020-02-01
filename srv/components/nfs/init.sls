include:
  - components.sspl.prepare
  - components.sspl.install
  - components.sspl.config
  - components.sspl.housekeeping
  #- components.sspl.sanity_check

Generate nfs checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.nfs
    - makedirs: True
    - create: True
