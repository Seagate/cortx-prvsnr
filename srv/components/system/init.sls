include:
  - components.system.prepare
  - components.system.install
  - components.system.config
  - components.system.housekeeping
#  - components.system.sanity_check
  - components.system.logrotate
  - components.system.ntp

Generate system checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.system
    - makedirs: True
    - create: True
