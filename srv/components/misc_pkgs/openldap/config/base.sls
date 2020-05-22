Configure OpenLDAP - Base config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/cfg_ldap.ldif

Remove existing file:
  cmd.run:
    - name: rm -f /etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif
    - require:
      - Configure OpenLDAP - Base config

Configure OpenLDAP - Schema:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/cn\=\{1\}s3user.ldif -H ldapi:///
    - require:
      - Remove existing file

Configure OpenLDAP - Base data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/ldap-init.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Schema

Configure OpenLDAP - Add IAM admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/iam-admin.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Base data

Configure OpenLDAP - Setup permissions for IAM admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/iam-admin-access.ldif
    - require:
      - Configure OpenLDAP - Add IAM admin

Configure OpenLDAP - Enable IAM constraints:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/iam-constraints.ldif
    - require:
      - Configure OpenLDAP - Setup permissions for IAM admin

Configure OpenLDAP - Load ppolicy schema:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -a -f /etc/openldap/schema/ppolicy.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Enable IAM constraints

Configure OpenLDAP - Load ppolicy module:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -a -f /opt/seagate/eos-prvsnr/generated_configs/ldap/ppolicymodule.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Load ppolicy schema

Configure OpenLDAP - Load ppolicy overlay:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -a -f /opt/seagate/eos-prvsnr/generated_configs/ldap/ppolicyoverlay.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Load ppolicy module

Configure OpenLDAP - password policy:
  cmd.run:
    - name: ldapmodify -x -a -H ldapi:/// -D cn=admin,dc=seagate,dc=com -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/ppolicy-default.ldif
    - require:
      - Configure OpenLDAP - Load ppolicy overlay

Configure OpenLDAP - Enable openldap log:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['admin']['secret'] }} -f /opt/seagate/eos-prvsnr/generated_configs/ldap/slapdlog.ldif

# Update openldap SSL certificates:
#   cmd.run:
#     - name: sh /opt/seagate/eos-prvsnr/generated_configs/ldap/enable_ssl_openldap.sh -cafile /etc/ssl/stx-s3/openldap/ca.crt -certfile /etc/ssl/stx-s3/openldap/s3openldap.crt -keyfile /etc/ssl/stx-s3/openldap/s3openldap.key
#     - require:
#       - Configure OpenLDAP - password policy

Restart Service Slapd:
  service.running:
    - name: slapd
