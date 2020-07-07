include:
  - components.misc_pkgs.openldap.start

Configure OpenLDAP - Base config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/cfg_ldap.ldif
    - watch_in:
      - Start sldapd service

Remove existing file:
  cmd.run:
    - name: rm -f /etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif
    - require:
      - Configure OpenLDAP - Base config
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Schema:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/cn\=\{1\}s3user.ldif -H ldapi:///
    - unless:
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn={1}s3user,cn=schema,cn=config"
    - require:
      - Remove existing file
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Base data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/ldap-init.ldif -H ldapi:///
    - unless:
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "dc=seagate,dc=com"
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "dc=s3,dc=seagate,dc=com"
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "ou=accounts,dc=s3,dc=seagate,dc=com"
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "ou=accesskeys,dc=s3,dc=seagate,dc=com"
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "ou=idp,dc=s3,dc=seagate,dc=com"
    - require:
      - Configure OpenLDAP - Schema
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Add IAM admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/iam-admin.ldif -H ldapi:///
    - unless:
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn=sgiamadmin,dc=seagate,dc=com"
    - require:
      - Configure OpenLDAP - Base data
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Setup permissions for IAM admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/iam-admin-access.ldif
    - require:
      - Configure OpenLDAP - Add IAM admin
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Enable IAM constraints:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/iam-constraints.ldif
    - unless:
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn=module{0},cn=config"
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "olcOverlay=unique,olcDatabase={2}{{ pillar['openldap']['backend_db'] }},cn=config"
    - require:
      - Configure OpenLDAP - Setup permissions for IAM admin
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Load ppolicy schema:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -a -f /etc/openldap/schema/ppolicy.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Enable IAM constraints
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Load ppolicy module:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -a -f /opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicymodule.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Load ppolicy schema
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Load ppolicy overlay:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -a -f /opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicyoverlay.ldif -H ldapi:///
    - require:
      - Configure OpenLDAP - Load ppolicy module
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - password policy:
  cmd.run:
    - name: ldapmodify -x -a -H ldapi:/// -D cn=admin,dc=seagate,dc=com -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicy-default.ldif
    - require:
      - Configure OpenLDAP - Load ppolicy overlay
    - watch_in:
      - Start sldapd service

Configure OpenLDAP - Enable openldap log:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['admin']['secret'] }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/slapdlog.ldif
    - watch_in:
      - Start sldapd service
