include:
  - components.s3server.openldap.install

create_dir_tmp_slapd:
  file.directory:
    - name: /tmp/s3ldap
    - clean: True
    - makedirs: True
    - force: True

generate_slapdpasswd_for_rootDN:
  cmd.run:
    - name: slappasswd -s {{ pillar['openldap']['openldappasswd'] }}
    - require:
      - pkg: install_pkgs

copy_initial_ldap_config:
  file.managed:
    - name: /tmp/s3ldap/cfg_ldap.ldif
    - source: salt://components/s3server/files/ldap/cfg_ldap.ldif
    - keep_source: False
    - template: jinja

copy_ldap_config:
  file.managed:
    - name: /tmp/s3ldap/iam-admin.ldif
    - source: salt://components/s3server/files/ldap/iam-admin.ldif
    - keep_source: False
    - template: jinja

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

# File copy operation
{% for filename in [
          { "src": 'salt://components/s3server/files/ldap/cn={1}s3user.ldif',
            "dest": '/tmp/s3ldap/cn={1}s3user.ldif' },
          { "src": 'salt://components/s3server/files/ldap/ldap-init.ldif',
            "dest": '/tmp/s3ldap/ldap-init.ldif' },
          { "src": 'salt://components/s3server/files/ldap/iam-admin-access.ldif',
          "dest": '/tmp/s3ldap/iam-admin-access.ldif' },
          { "src": 'salt://components/s3server/files/ldap/syncprov-mod.ldif',
          "dest": '/tmp/s3ldap/syncprov-mod.ldif' },
          { "src": 'salt://components/s3server/files/ldap/syncprov.ldif',
          "dest": '/tmp/s3ldap/syncprov.ldif' },
          { "src": 'salt://components/s3server/files/ldap/ssl/ssl_certs.ldif',
          "dest": '/tmp/s3ldap/ssl_certs.ldif' },
          { "src": 'salt://components/s3server/files/ldap/ssl/ldap.conf',
          "dest": '/etc/openldap/ldap.conf' }] %}
{{ filename.dest }}:
  file.managed:
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
    - watch_in:
      - service: slapd
{% endfor %}

slapd:
  service.running:
    - enable: True
