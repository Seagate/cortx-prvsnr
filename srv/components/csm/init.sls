include:
  - components.csm.prepare
  - components.csm.install
  - components.csm.config
  - components.csm.start
  - components.csm.sanity_check

Generate csm checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.csm
    - makedirs: True
    - create: True
