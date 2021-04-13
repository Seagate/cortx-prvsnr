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
  - components.misc_pkgs.openldap.start

{% set ldap_password = salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) %}
Configure OpenLDAP - Base config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/cfg_ldap.ldif
    - env:
      - password: {{ ldap_password }}
    - watch_in:
      - Restart slapd service

Remove existing file:
  cmd.run:
    - name: rm -f /etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif
    - require:
      - Configure OpenLDAP - Base config
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Schema:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,cn=config" -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/cn\=\{1\}s3user.ldif -H ldapi:///
    - env:
      - password: {{ ldap_password }}
    # - unless:
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn={1}s3user,cn=schema,cn=config"
    - require:
      - Remove existing file
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Base data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/ldap-init.ldif -H ldapi:///
    # - unless:
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "dc=seagate,dc=com"
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "dc=s3,dc=seagate,dc=com"
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "ou=accounts,dc=s3,dc=seagate,dc=com"
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "ou=accesskeys,dc=s3,dc=seagate,dc=com"
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "ou=idp,dc=s3,dc=seagate,dc=com"
    - env:
      - password: {{ ldap_password }}
    - require:
      - Configure OpenLDAP - Schema
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Add IAM admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/iam-admin.ldif -H ldapi:///
    - env:
      - password: {{ ldap_password }}
    # - unless:
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn=sgiamadmin,dc=seagate,dc=com"
    - require:
      - Configure OpenLDAP - Base data
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Setup permissions for IAM admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/iam-admin-access.ldif
    - env:
      - password: {{ ldap_password }}
    - require:
      - Configure OpenLDAP - Add IAM admin
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Enable IAM constraints:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/iam-constraints.ldif
    - env:
      - password: {{ ldap_password }}
    # - unless:
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn=module{0},cn=config"
    #   - ldapsearch -x -w {{ salt['lyveutils.decrypt']('cortx', pillar['cortx']['software']['openldap']['root']['secret']) }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "olcOverlay=unique,olcDatabase={2}{{ pillar['cortx']['software']['openldap']['backend_db'] }},cn=config"
    - require:
      - Configure OpenLDAP - Setup permissions for IAM admin
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Load ppolicy schema:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w $password -a -f /etc/openldap/schema/ppolicy.ldif -H ldapi:///
    - env:
      - password: {{ ldap_password }}
    - require:
      - Configure OpenLDAP - Enable IAM constraints
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Load ppolicy module:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w $password -a -f /opt/seagate/cortx_configs/provisioner_generated/ldap/ppolicymodule.ldif -H ldapi:///
    - env:
      - password: {{ ldap_password }}
    - require:
      - Configure OpenLDAP - Load ppolicy schema
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Load ppolicy overlay:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w $password -a -f /opt/seagate/cortx_configs/provisioner_generated/ldap/ppolicyoverlay.ldif -H ldapi:///
    - env:
      - password: {{ ldap_password }}
    - require:
      - Configure OpenLDAP - Load ppolicy module
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - password policy:
  cmd.run:
    - name: ldapmodify -x -a -H ldapi:/// -D cn=admin,dc=seagate,dc=com -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/ppolicy-default.ldif
    - env:
      - password: {{ ldap_password }}
    - require:
      - Configure OpenLDAP - Load ppolicy overlay
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Enable openldap log:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/slapdlog.ldif
    - env:
      - password: {{ ldap_password }}
    - watch_in:
      - Restart slapd service

Configure OpenLDAP - Set ldap results set size:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w $password -f /opt/seagate/cortx_configs/provisioner_generated/ldap/resultssizelimit.ldif
    - env:
      - password: {{ ldap_password }}
    - watch_in:
      - Restart slapd service
