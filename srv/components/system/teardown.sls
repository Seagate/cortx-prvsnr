# Remove_base_packages:
#   pkg.purged:
#     - pkgs:
#       - python2-pip
#       - python36-pip
#       - vi-enhanced
#       - tmux

Remove cryptography pip package:
  pip.removed:
    - name: cryptography
    - bin_env: /usr/bin/pip3

Remove eos-py-utils pip package:
  pkg.purged:
    - name: eos-py-utils

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

Remove added journald configuration:
  file.replace:
    - name: /etc/systemd/journald.conf
    - pattern: "^Storage=persistent.*?MaxRetentionSec=1week"
    - flags: ['MULTILINE', 'DOTALL']
    - repl: ''
    - ignore_if_missing: True

restart systemd-journald:
  module.run:
    - service.restart:
      - systemd-journald

Remove /var/log/journal:
  file.absent:
    - name: /var/log/journal

Restart systemd-journald:
  module.run:
    - service.restart:
      - systemd-journald

