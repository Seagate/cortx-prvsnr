include:
  - components.misc_pkgs.rabbitmq
  - components.sspl.prepare
  - components.sspl.install
  - components.sspl.config
  - components.sspl.start
#  - components.sspl.sanity_check

Generate sspl checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.sspl
    - makedirs: True
    - create: True
