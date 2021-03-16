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

{% import_yaml 'components/defaults.yaml' as defaults %}
Stage - Reset CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/csm/conf/setup.yaml', 'csm:reset')

Remove csm package:
  pkg.purged:
    - pkgs:
      - cortx-cli
      - cortx-csm_agent
      - cortx-csm_web

Delete CSM yum repo:
  pkgrepo.absent:
    - name: {{ defaults.csm.repo.id }}

Delete CSM uploads repo:
  pkgrepo.absent:
    - name: {{ defaults.csm.uploads_repo.id }}

Remove stats collector:
  file.absent:
    - name: /opt/statsd/csm-stats-collector

Remove Symlink:
  file.absent:
    - name: /usr/bin/csm-stats-collector

Remove crontab:
  cron.absent:
    - name: /opt/statsd/csm-stats-collector 10
    - user: root
    - identifier: csm-stats-collector

Delete csm checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.csm

# TODO TEST
Remove csm user from prvsnrusers group:
  group.present:
    - name: prvsnrusers
    - delusers:
      - csm

Remove csm user from certs group:
  group.present:
    - name: certs
    - delusers:
      - csm
