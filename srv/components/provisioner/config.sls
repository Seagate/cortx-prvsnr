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

# TODO IMPROVE salt configs might go here as well
include:
  - components.misc_pkgs.rsyslog
  - components.system.config.pillar_encrypt

provisioner_rsyslog_conf_updated:
  file.managed:
    - name: /etc/rsyslog.d/prvsnrfwd.conf
    - source: salt://components/provisioner/files/prvsnrfwd.conf
    - makedirs: True
    - watch_in:
      - service: Start rsyslog

{% if 'single' not in pillar['cluster']['type'] %}
# Always start glusterfshsaredstorage before salt-master
Update glusterfssharedstorage.service:
  file.managed:
    - name: /usr/lib/systemd/system/glusterfssharedstorage.service
    - source: salt://components/provisioner/files/glusterfshsaredstorage.service
    
Update salt-master.service:
  file.managed:
    - name: /usr/lib/systemd/system/salt-master.service
    - source: salt://components/provisioner/salt_master/files/salt-master.service

Reload updated services:
  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - file: Update salt-master.service
{% endif %}
