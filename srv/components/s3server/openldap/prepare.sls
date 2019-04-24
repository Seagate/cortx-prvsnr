Remove existing certs:
  pkg.removed:
    - pkgs:
      - stx-s3-certs
      - stx-s3-client-certs

create_dir_tmp_slapd:
  file.directory:
    - name: /tmp/s3ldap
    - clean: True
    - makedirs: True
    - force: True

copy_initial_ldap_config:
  file.managed:
    - name: /tmp/s3ldap/cfg_ldap.ldif
    - source: salt://components/s3server/files/openldap/cfg_ldap.ldif
    - keep_source: False
    - template: jinja

copy_ldap_config:
  file.managed:
    - name: /tmp/s3ldap/iam-admin.ldif
    - source: salt://components/s3server/files/openldap/iam-admin.ldif
    - keep_source: False
    - template: jinja

# File copy operation
{% for filename in [
          { "src": 'salt://components/s3server/files/openldap/cn={1}s3user.ldif',
            "dest": '/tmp/s3ldap/cn={1}s3user.ldif' },
          { "src": 'salt://components/s3server/files/openldap/ldap-init.ldif',
            "dest": '/tmp/s3ldap/ldap-init.ldif' },
          { "src": 'salt://components/s3server/files/openldap/iam-admin-access.ldif',
          "dest": '/tmp/s3ldap/iam-admin-access.ldif' },
          { "src": 'salt://components/s3server/files/openldap/syncprov-mod.ldif',
          "dest": '/tmp/s3ldap/syncprov-mod.ldif' },
          { "src": 'salt://components/s3server/files/openldap/syncprov.ldif',
          "dest": '/tmp/s3ldap/syncprov.ldif' },
          { "src": 'salt://components/s3server/files/openldap/ssl/ssl_certs.ldif',
          "dest": '/tmp/s3ldap/ssl_certs.ldif' },
          { "src": 'salt://components/s3server/files/openldap/ssl/ldap.conf',
          "dest": '/etc/openldap/ldap.conf' }] %}
{{ filename.dest }}:
  file.managed:
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
{% endfor %}
