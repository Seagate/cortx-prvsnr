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

{% set ldap_pkgs = ['symas-openldap', 'symas-openldap-clients'] -%}
{% for ldap_pkg in ldap_pkgs %}
{% if not salt['cmd.run']('rpm -qa {{ ldap_pkg }}') %}

Install openldap pkg {{ ldap_pkg }}:
  pkg.installed:
    - pkgs:
      - {{ ldap_pkg }}
    {% if "openldap_server" in pillar["cluster"][grains['id']]["roles"] %}
      - symas-openldap-servers
    {% endif %}

{%- else -%}
OpenLDAP pkg {{ ldap_pkg }} already installed:
  test.show_notification:
    - text: "OpenLDAP dependent package {{ ldap_pkg }} is already installed"
{% endif %}
{% endfor %}

Update to latest selinux-policy:
  pkg.installed:
    - name: selinux-policy

# FIXME EOS-12076 the following steps are about configuration, not installation

{% if "openldap_server" in pillar["cluster"][grains['id']]["roles"] %}
Backup slapd config file:
  file.copy:
    - name: /etc/sysconfig/slapd.bak
    - source: /etc/sysconfig/slapd
    - force: True
    - preserve: True
{% endif %}

Generate Slapdpasswds:
  cmd.run:
    - name: sh /opt/seagate/cortx_configs/provisioner_generated/ldap/ldap_gen_passwd.sh

Stop slapd:
  service.dead:
    - name: slapd

Add password file to ldap group:
  cmd.run:
    - name: chgrp ldap /etc/openldap/certs/password
    - onlyif: grep -q ldap /etc/group && test -f /etc/openldap/certs/password

{% if "openldap_server" in pillar["cluster"][grains['id']]["roles"] %}
{% if 'mdb' in pillar['cortx']['software']['openldap']['backend_db'] %}
Clean up old mdb ldiff file:
  file.absent:
    - name: /etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif

Copy mdb ldiff file, if not present:
  file.copy:
    - name: /etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif
    - source: /opt/seagate/cortx_configs/provisioner_generated/ldap/olcDatabase={2}mdb.ldif
    - force: True
    - user: ldap
    - group: ldap
    - watch_in:
      - service: slapd
{% endif %}

slapd:
  service.running:
    - enable: True
{% endif %}
