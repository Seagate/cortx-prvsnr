include:
  - components.system.logrotate.teardown

install_base_packages:
  pkg.absent:
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
