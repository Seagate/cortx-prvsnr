include:
  - components.system.logrotate.teardown
  - components.system.ntp.teardown
  - components.system.firewall.teardwon

Remove_base_packages:
  pkg.purged:
    - pkgs:
      - python2-pip
      - python36-pip
      # - vi-enhanced
      # - tmux

clean_yum_local:
  cmd.run:
    - name: yum clean all

{% import_yaml 'components/defaults.yaml' as defaults %}
Delete Commons yum repo:
  pkgrepo.absent:
    - name: {{ defaults.commons.repo.id }}

Delete system checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.system

