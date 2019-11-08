Remove existing certs:
  pkg.removed:
    - pkgs:
      - stx-s3-certs
      - stx-s3-client-certs

Create tmp dir:
  file.directory:
    - name: /opt/seagate/generated_configs/ldap
    - clean: True
    - makedirs: True
    - force: True

Copy initial ldap config:
  file.managed:
    - name: /opt/seagate/generated_configs/ldap/cfg_ldap.ldif
    - source: salt://components/misc/openldap/files/cfg_ldap.ldif

Copy ldap config:
  file.managed:
    - name: /opt/seagate/generated_configs/ldap/iam-admin.ldif
    - source: salt://components/misc/openldap/files/iam-admin.ldif

Copy ldap_gen_passwd script:
  file.managed:
    - name: /opt/seagate/generated_configs/ldap/ldap_gen_passwd.sh
    - source: salt://components/misc/openldap/files/ldap_gen_passwd.sh
    - keep_source: False
    - user: root
    - group: root
    - mode: 755
    - makedirs: True
    - template: jinja

Copy ldap enable ssl script:
  file.managed:
    - name: /opt/seagate/generated_configs/ldap/enable_ssl_openldap.sh
    - source: salt://components/misc/openldap/files/ssl/enable_ssl_openldap.sh
    - keep_source: False
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

{% if pillar['cluster']['type'] == "ees" %}
Copy ldap replication config:
  file.managed:
    - name: /opt/seagate/generated_configs/ldap/replicate.ldif
    - source: salt://components/misc/openldap/files/replicate.ldif
    - keep_source: False
    - template: jinja
{% endif %}

# File copy operation
{% for filename in [
    { "src": 'salt://components/misc/openldap/files/cn={1}s3user.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/cn={1}s3user.ldif' },
    { "src": 'salt://components/misc/openldap/files/ldap-init.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/ldap-init.ldif' },
    { "src": 'salt://components/misc/openldap/files/iam-admin-access.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/iam-admin-access.ldif' },
    { "src": 'salt://components/misc/openldap/files/iam-constraints.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/iam-constraints.ldif' },
    { "src": 'salt://components/misc/openldap/files/olcDatabase={2}mdb.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/olcDatabase={2}mdb.ldif' },
    { "src": 'salt://components/misc/openldap/files/syncprov_mod.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/syncprov_mod.ldif' },
    { "src": 'salt://components/misc/openldap/files/syncprov.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/syncprov.ldif' },
    { "src": 'salt://components/misc/openldap/files/ssl/ssl_certs.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/ssl_certs.ldif' },
    { "src": 'salt://components/misc/openldap/files/ppolicy-default.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/ppolicy-default.ldif'},
    { "src": 'salt://components/misc/openldap/files/ppolicymodule.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/ppolicymodule.ldif'},
    { "src": 'salt://components/misc/openldap/files/ppolicyoverlay.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/ppolicyoverlay.ldif'},
    { "src": 'salt://components/misc/openldap/files/test_data.ldif',
      "dest": '/opt/seagate/generated_configs/ldap/test_data.ldif' },
    { "src": 'salt://components/misc/openldap/files/ssl/ldap.conf',
      "dest": '/etc/openldap/ldap.conf' },
    ]
%}
{{ filename.dest }}:
  file.managed:
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
{% endfor %}
