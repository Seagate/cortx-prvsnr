#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

Remove_base_packages:
  pkg.purged:
    - pkgs:
      - ipmitool
      - bind-utils
      - python3
      - rsync
      - ftp
      - sshpass
      - jq
      - policycoreutils 
      - policycoreutils-python
      - python3-pip
#     - python2-pip
#     - python36-pip
#     - vi-enhanced
#     - tmux

Remove cryptography pip package:
  pip.removed:
    - name: cryptography
    - bin_env: /usr/bin/pip3

Remove cortx-py-utils pip package:
  pkg.purged:
    - name: cortx-py-utils

clean_yum_local:
  cmd.run:
    - name: yum clean all

{% import_yaml 'components/defaults.yaml' as defaults %}
Delete Commons yum repo:
  pkgrepo.absent:
    - name: {{ defaults.commons.repo.id }}

Remove added journald configuration:
  file.replace:
    - name: /etc/systemd/journald.conf
    - pattern: "^Storage=persistent"
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

Delete system checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.system
