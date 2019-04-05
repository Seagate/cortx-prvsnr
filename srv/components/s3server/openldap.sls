
# Kind of slapd cleanup from here
stop_slapd:
  service.dead:
    - name: slapd

remove_pkgs:
  pkg.purged:
    - pkgs:
      - openldap-servers
      - openldap-clients
      - stx-s3-certs
      - stx-s3-client-certs
    - require:
      - stop_slapd

# File cleanup operation
{% for filename in [
   '/etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif',
   '/var/lib/ldap/*',
   '/etc/sysconfig/slapd*',
   '/etc/openldap/slapd.d/*',
   '/etc/openldap/slapd*',
   rpm_build_dir + "/stx-s3-certs*",
   rpm_build_dir + "/stx-s3-client-certs*"
 ] %}

{{ filename }}:
  file.absent:
    - require:
      - pkg: remove_pkgs

{% endfor %}

install_pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients

create_dir_tmp_slapd:
  file.directory:
    - name: /tmp/s3ldap
    - makedirs: True

generate_slapdpasswd_for_rootDN:
  cmd.run:
    - name: slappasswd -s {{ salt['pillar.get']('components.s3server.openldap.openldappasswd') }}
    - require:
      - pkg: install_pkgs

copy_initial_ldap_config:
  file.managed:
    - name: /tmp/s3ldap/cfg_ldap.ldif
    - source: salt://components/install/s3server/files/ldap/cfg_ldap.ldif
    - keep_source: False
    - template: jinja

copy_ldap_config:
  file.managed:
    - name: /tmp/s3ldap/iam-admin.ldif
    - source: salt://components/install/s3server/files/ldap/iam-admin.ldif
    - keep_source: False
    - template: jinja

# File copy operation
{% for filename in [
          { src: 'salt://components/install/s3server/files/ldap/cn\=\{1\}s3user.ldif',
            dest: '/tmp/s3ldap/cn\=\{1\}s3user.ldif' },
          { src: 'salt://components/install/s3server/files/ldap/ldap-init.ldif',
            dest: '/tmp/s3ldap/ldap-init.ldif' },
          { src: 'salt://components/install/s3server/files/ldap/iam-admin-access.ldif',
          dest: '/tmp/s3ldap/iam-admin-access.ldif' },
          { src: 'salt://components/install/s3server/files/ldap/syncprov_mod.ldif',
          dest: '/tmp/s3ldap/syncprov_mod.ldif' },
          { src: 'salt://components/install/s3server/files/ldap/syncprov.ldif',
          dest: '/tmp/s3ldap/syncprov.ldif' }] %}

{{ filename.dest }}:
  file.copy:
    - source: {{ filename.src }}
    - force: True
    - makedirs: True

{% endfor %}

slapd:
  service.running:
    - enable: true

configure_openLDAP_base_config:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap:openldappasswd'] }} -f /tmp/s3ldap/cfg_ldap.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: slapd

configure_openLDAP_schema:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin, cn=config' -w {{ pillar['openldap:openldappasswd'] }} -f /tmp/s3ldap/cn=\{1\}s3user.ldif
    - cwd: /tmp/s3ldap/
    - watch_in:
      - service: slapd

configure_openLDAP_base_data:
  cmd.run:
    - name: ldapadd -x -D "cn=admin,dc=seagate,dc=com" -w {{ pillar['openldap:openldappasswd'] }} -f /tmp/s3ldap/ldap-init.ldif
  no_log: true
    - watch_in:
      - service: slapd
configure_openLDAP_add_IAM_admin:
  cmd.run:
    - name: ldapadd -x -D 'cn=admin,dc=seagate,dc=com' -w {{ pillar['openldap:openldappasswd'] }} -f /tmp/s3ldap/iam-admin.ldif
    - watch_in:
      - service: slapd

configure_openLDAP_setup_permissions_for_IAM_admin:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ pillar['openldap:openldappasswd'] }} -f /tmp/s3ldap/iam-admin-access.ldif
    - watch_in:
      - service: slapd

copy_SSL_config_file_for_openldap:
  file.copy:
    - name: /tmp/s3ldap/ssl_certs.ldif
    - source: salt://components/install/s3server/files/ldap/ssl/ssl_certs.ldif
    - force: True
    - makedirs: True

update_openldap_configuration:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL  -H ldapi:/// -f /tmp/s3ldap/ssl_certs.ldif
    - watch_in:
      - service: slapd

backup_original_slapd_file:
  file.copy:
    - name: /etc/sysconfig/slapd.bak
    - source: /etc/sysconfig/slapd
    - force: True
    - preserve: True

add_ssl_nonssl_ldap_uri:
  cmd.run:
    - name: sed -i "s/^SLAPD_URLS=.*/SLAPD_URLS={{ pillar['openldap:ldap_url'] }}/" /etc/sysconfig/slapd

backup_ldap_conf:
  file.copy:
    - name: /etc/openldap/ldap.conf.bak
    - source: /etc/openldap/ldap.conf
    - force: True
    - preserve: True

setup_ssl_config_for_ldap_client_tools:
  file.copy:
    - name: /etc/openldap/ldap.conf
    - source: salt://components/install/s3server/files/ldap/ssl/ldap.conf
    - force: True
    - watch_in:
      - service: slapd

delete_dir_tmp_slapd:
  file.absent:
    - name: /tmp/s3ldap
