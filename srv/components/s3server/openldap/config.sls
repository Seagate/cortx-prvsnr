backup_ldap_conf:
  file.copy:
    - name: /etc/openldap/ldap.conf.bak
    - source: /etc/openldap/ldap.conf
    - force: True
    - preserve: True

backup_original_slapd_file:
  file.copy:
    - name: /etc/sysconfig/slapd.bak
    - source: /etc/sysconfig/slapd
    - force: True
    - preserve: True

generate_slapdpasswd_for_rootDN:
  cmd.run:
    - name: slappasswd -s {{ pillar['openldap']['openldappasswd'] }}
    - require:
      - service: slapd_service

base_config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/cfg_ldap.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: slapd_service

openLDAP_schema:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,cn=config" -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/cn={1}s3user.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: slapd_service

base_data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/ldap-init.ldif
    - watch_in:
      - service: slapd_service

add_IAM_admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/iam-admin.ldif
    - watch_in:
      - service: slapd_service

setup_permissions_for_IAM_admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap']['openldappasswd'] }} -f /tmp/s3ldap/iam-admin-access.ldif
    - watch_in:
      - service: slapd_service

update_openldap_configuration:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -f /tmp/s3ldap/ssl_certs.ldif
    - watch_in:
      - service: slapd_service

add_ssl_nonssl_ldap_uri:
  cmd.run:
    - name: sed -i "s/^SLAPD_URLS=.*/SLAPD_URLS={{ pillar['openldap']['ldap_url'] }}/" /etc/sysconfig/slapd

slapd_service:
  service.running:
    - name: slapd
