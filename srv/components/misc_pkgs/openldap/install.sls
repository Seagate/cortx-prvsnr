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

Install openldap pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients

Update to latest selinux-policy:
  pkg.installed:
    - name: selinux-policy

Backup slapd config file:
  file.copy:
    - name: /etc/sysconfig/slapd.bak
    - source: /etc/sysconfig/slapd
    - force: True
    - preserve: True

Generate Slapdpasswds:
   cmd.run:
     - name: sh /opt/seagate/cortx/provisioner/generated_configs/ldap/ldap_gen_passwd.sh

Stop slapd:
  service.dead:
    - name: slapd

Add password file to ldap group:
  cmd.run:
    - name: chgrp ldap /etc/openldap/certs/password
    - onlyif: grep -q ldap /etc/group && test -f /etc/openldap/certs/password

{% if 'mdb' in pillar['openldap']['backend_db'] %}
Clean up old mdb ldiff file:
  file.absent:
    - name: /etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif

Copy mdb ldiff file, if not present:
  file.copy:
    - name: /etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif
    - source: /opt/seagate/cortx/provisioner/generated_configs/ldap/olcDatabase={2}mdb.ldif
    - force: True
    - user: ldap
    - group: ldap
    - watch_in:
      - service: slapd
{% endif %}

slapd:
  service.running:
    - enable: True
