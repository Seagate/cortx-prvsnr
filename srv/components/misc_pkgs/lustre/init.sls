include:
  - components.misc_pkgs.lustre.prepare
  - components.misc_pkgs.lustre.install
  - components.misc_pkgs.lustre.config
  - components.misc_pkgs.lustre.start
  - components.misc_pkgs.lustre.sanity_check

Generate lustre checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.lustre
    - makedirs: True
    - create: True
