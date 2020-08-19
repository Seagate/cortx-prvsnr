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

include:
  - components.ha.corosync-pacemaker.install

# HA user has to be updated for setting new password.
# This has to happen only after pacemaker is installed.
Update ha user:
  user.present:
    - name: {{ pillar['corosync-pacemaker']['user'] }}
    - password: {{ salt['lyveutil.decrypt']('corosync-pacemaker', pillar['corosync-pacemaker']['secret']) }}
    - hash_password: True
    - createhome: False
    - shell: /sbin/nologin

#Configurations for Corosync and Pacemaker Setup
Add hacluster user to haclient group:
  group.present:
    - name: haclient
    - addusers:
      - {{ pillar['corosync-pacemaker']['user'] }}

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
