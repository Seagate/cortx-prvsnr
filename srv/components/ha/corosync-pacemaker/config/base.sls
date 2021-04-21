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

include:
  - components.ha.corosync-pacemaker.install

# HA user has to be updated for setting new password.
# This has to happen only after pacemaker is installed.
Update ha user:
  user.present:
    - name: {{ pillar['cortx']['software']['corosync-pacemaker']['user'] }}
    - password: {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['corosync-pacemaker']['secret']) }}
    - hash_password: True
    - createhome: False
    - shell: /sbin/nologin

#Configurations for Corosync and Pacemaker Setup
Add hacluster user to haclient group:
  group.present:
    - name: haclient
    - addusers:
      - {{ pillar['cortx']['software']['corosync-pacemaker']['user'] }}

Enable corosync service:
  service.dead:
    - name: corosync
    - enable: True
    - require:
      - Install corosync

Enable pacemaker service:
  service.dead:
    - name: pacemaker
    - enable: True
    - require:
      - Install pacemaker

Start pcsd service:
  service.running:
    - name: pcsd
    - enable: True
    - require:
      - Install pcs
