include:
  - components.misc_pkgs.lustre
  - components.eoscore.prepare
  - components.eoscore.install
  - components.eoscore.config
  # - components.eoscore.start
  - components.eoscore.sanity_check

Generate eoscore checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.eoscore
    - makedirs: True
    - create: True
