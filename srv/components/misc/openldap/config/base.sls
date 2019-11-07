Backup ldap config file:
  file.copy:
    - name: /etc/openldap/ldap.conf.bak
    - source: /etc/openldap/ldap.conf
    - force: True
    - preserve: True

Backup slapd config file:
  file.copy:
    - name: /etc/sysconfig/slapd.bak
    - source: /etc/sysconfig/slapd
    - force: True
    - preserve: True

Clean up old mdb ldiff file:
  file.absent:
    - name: /etc/openldap/slapd.d/cn\=config/olcDatabase\=\{2\}mdb.ldif

Copy mdb ldiff file, if not present:
  file.copy:
    - name: /etc/openldap/slapd.d/cn\=config/olcDatabase\=\{2\}mdb.ldif
    - source: /opt/seagate/generated_configs/ldap/olcDatabase\=\{2\}mdb.ldif
    - force: True
    - preserve: True
    - user: ldap
    - group: ldap

generate_slapdpasswds:
   cmd.run:
     - name: /opt/seagate/scripts/ldap_gen_passwd.sh

Configure OpenLDAP - Base config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['admin_passwd'] }} -f /opt/seagate/generated_configs/ldap/cfg_ldap.ldif
    - require:
      - generate_slapdpasswds
    - watch_in:
      - service: Service Slapd

Remove existing file:
  cmd.run:
    - name: rm -f /etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif
    - require:
      - Configure OpenLDAP - Base config

Configure OpenLDAP - Schema:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,cn=config" -w {{ pillar['openldap']['admin_passwd'] }} -f /opt/seagate/generated_configs/ldap/cn\=\{1\}s3user.ldif
    - require:
      - Remove existing file

Configure OpenLDAP - Base data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w {{ pillar['openldap']['admin_passwd'] }} -f /opt/seagate/generated_configs/ldap/ldap-init.ldif
    - require:
      - Configure OpenLDAP - Schema

Configure OpenLDAP - Add IAM admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w {{ pillar['openldap']['admin_passwd'] }} -f /opt/seagate/generated_configs/ldap/iam-admin.ldif
    - require:
      - Configure OpenLDAP - Base data

Configure OpenLDAP - Setup permissions for IAM admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['admin_passwd'] }} -f /opt/seagate/generated_configs/ldap/iam-admin-access.ldif
    - require:
      - Configure OpenLDAP - Add IAM admin

Configure OpenLDAP - Enable IAM constraints:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['admin_passwd'] }} -f /opt/seagate/generated_configs/ldap/iam-constraints.ldif
    - require:
      - Configure OpenLDAP - Setup permissions for IAM admin

Configure OpenLDAP - Load ppolicy schema:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ pillar['openldap']['admin_passwd'] }} -a -f /etc/openldap/schema/ppolicy.ldif
    - require:
      - Configure OpenLDAP - Enable IAM constraints

Configure OpenLDAP - Load ppolicy module:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ pillar['openldap']['admin_passwd'] }} -a -f /opt/seagate/generated_configs/ldap/ppolicymodule.ldif
    - require:
      - Configure OpenLDAP - Load ppolicy schema

Configure OpenLDAP - Load ppolicy overlay:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ pillar['openldap']['admin_passwd'] }} -a -f /opt/seagate/generated_configs/ldap/ppolicyoverlay.ldif
    - require:
      - Configure OpenLDAP - Load ppolicy module

Configure OpenLDAP - password policy:
  cmd.run:
    - name: ldapmodify -x -a -H ldapi:/// -D cn=admin,dc=seagate,dc=com -w {{ pillar['openldap']['admin_passwd'] }} -f /opt/seagate/generated_configs/ldap/ppolicy-default.ldif
    - require:
      - Configure OpenLDAP - Load ppolicy overlay

Update openldap SSL certificates:
  cmd.run:
    - name: /opt/seagate/scripts/enable_ssl_openldap.sh -cafile /etc/ssl/stx-s3/openldap/ca.crt -certfile /etc/ssl/stx-s3/openldap/s3openldap.crt -keyfile /etc/ssl/stx-s3/openldap/s3openldap.key
    - require:
      - Configure OpenLDAP - password policy

Service Slapd:
  service.running:
    - name: slapd
    - full_restart: True
