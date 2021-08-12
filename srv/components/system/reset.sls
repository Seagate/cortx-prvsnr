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

Remove cortx-py-utils dependencies:
  pip.removed:
    - requirements: salt://components/system/files/cortx_py_utils_requirements.txt
    - bin_env: /usr/bin/pip3

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

Remove /var/log/crash:
  file.absent:
    - name: /var/log/crash

Remove coredumps_rotate cron.hourly:
  file.absent:
    - name: /etc/cron.hourly/coredumps_rotate

Restart systemd-journald:
  module.run:
    - service.restart:
      - systemd-journald

Delete system checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.system

#Remove wheel access from sudoers:
#  file.absent:
#    - name: /etc/sudoers.d/wheel_access
