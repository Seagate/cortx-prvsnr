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

base_config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/cfg_ldap.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: Service Slapd

openLDAP_schema:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,cn=config" -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/cn={1}s3user.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: Service Slapd

base_data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/ldap-init.ldif
    - watch_in:
      - service: Service Slapd

add_IAM_admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/iam-admin.ldif
    - watch_in:
      - service: Service Slapd

Setup permissions for IAM admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/iam-admin-access.ldif
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
