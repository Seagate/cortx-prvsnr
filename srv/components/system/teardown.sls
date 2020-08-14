#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

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
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.system

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
