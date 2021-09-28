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

salt_master_config_updated:
  file.managed:
    - name: /etc/salt/master
    - source: salt://components/provisioner/salt_master/files/master
    - template: jinja

# Always start glusterfshsaredstorage before salt-master
Update glusterfssharedstorage.service:
  file.managed:
    - name: /usr/lib/systemd/system/glusterfssharedstorage.service
    - source: salt://components/provisioner/files/glusterfshsaredstorage.service

Restart GlusterFSSharedStorage service:
  service.running:
    - name: glusterfssharedstorage
    - enabled: True
    - watch:
      - Update glusterfssharedstorage.service

Update salt-master.service:
  file.managed:
    - name: /usr/lib/systemd/system/salt-master.service
    - source: salt://components/provisioner/salt_master/files/salt-master.service

Reload updated services:
  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - file: Update salt-master.service
      - file: Update glusterfssharedstorage.service

salt_master_service_enabled:
  service.enabled:
    - name: salt-master
    - require:
      - file: salt_master_config_updated

# Note. salt-master restart is in foreground,
# so salt-minion will reported to restarted salt-master
salt_master_service_restarted:
  cmd.run:
    # 1. test.true will prevent restart of salt-master if the config is malformed
    # 2. --local is required if salt-master is actually not running,
    #    since state might be called by salt-run as well
    - name: 'salt-run salt.cmd test.true > /dev/null && salt-call --local service.restart salt-master > /dev/null '
    - bg: True
    - onchanges:
      - file: salt_master_config_updated
      - file: Update salt-master.service
