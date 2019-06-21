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

# generate_slapdpasswd_for_rootDN:
#   cmd.run:
#     - name: slappasswd -s {{ pillar['openldap']['openldappasswd'] }}
#     - require:
#       - service: Service Slapd

Configure OpenLDAP - Base config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/cfg_ldap.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: Service Slapd

Configure OpenLDAP - Schema:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,cn=config" -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/cn={1}s3user.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: Service Slapd

Configure OpenLDAP - Base data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/ldap-init.ldif
    - watch_in:
      - service: Service Slapd

Configure OpenLDAP - Add IAM admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/iam-admin.ldif
    - watch_in:
      - service: Service Slapd

Configure OpenLDAP - Setup permissions for IAM admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/iam-admin-access.ldif
    - watch_in:
      - service: Service Slapd

Configure OpenLDAP - Enable IAM constraints:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/iam-constraints.ldif
    - watch_in:
      - service: Service Slapd

Configure OpenLDAP - Load ppolicy schema:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ pillar['openldap']['openldappasswd'] }} -a -f /etc/openldap/schema/ppolicy.ldif
    - watch_in:
      - service: Service Slapd


Configure OpenLDAP - Load ppolicy module:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ pillar['openldap']['openldappasswd'] }} -a -f /tmp/s3ldap/ppolicymodule.ldif
    - watch_in:
      - service: Service Slapd


Configure OpenLDAP - Load ppolicy overlay:
  cmd.run:
    - name: ldapmodify -D "cn=admin,cn=config" -w {{ pillar['openldap']['openldappasswd'] }} -a -f /tmp/s3ldap/ppolicyoverlay.ldif
    - watch_in:
      - service: Service Slapd


Configure OpenLDAP - Configure password policy:
  cmd.run:
    - name: ldapmodify -x -a -H ldapi:/// -D cn=admin,dc=seagate,dc=com -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/ppolicy-default.ldif
    - watch_in:
      - service: Service Slapd

Update openldap configuration:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -f /tmp/s3ldap/ssl_certs.ldif
    - watch_in:
      - service: Service Slapd

Add ssl nonssl ldap uri:
  cmd.run:
    - name: sed -i "s/^SLAPD_URLS=.*/SLAPD_URLS={{ pillar['openldap']['ldap_url'] }}/" /etc/sysconfig/slapd

Service Slapd:
  service.running:
    - name: slapd
