include:
  - components.system.prepare
  - components.system.install
  - components.system.pillar_encrypt
  - components.system.config
  - components.system.housekeeping
  - components.system.sanity_check
  # - components.system.firewall
  # - components.system.logrotate
  # - components.system.ntp

Generate system checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.system
    - makedirs: True
    - create: True
