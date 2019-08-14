Remove existing certs:
  pkg.removed:
    - pkgs:
      - stx-s3-certs
      - stx-s3-client-certs

Delete tmp dir:
  file.absent:
    - name: /tmp/s3ldap

Create tmp dir:
  file.directory:
    - name: /tmp/s3ldap
    - clean: True
    - makedirs: True
    - force: True

Copy initial ldap config:
  file.managed:
    - name: /tmp/s3ldap/cfg_ldap.ldif
    - source: salt://components/misc/openldap/files/cfg_ldap.ldif
    - keep_source: False
    - template: jinja

Copy ldap config:
  file.managed:
    - name: /tmp/s3ldap/iam-admin.ldif
    - source: salt://components/misc/openldap/files/iam-admin.ldif
    - keep_source: False
    - template: jinja

# File copy operation
{% for filename in [
    { "src": 'salt://components/misc/openldap/files/cn={1}s3user.ldif',
      "dest": '/tmp/s3ldap/cn={1}s3user.ldif' },
    { "src": 'salt://components/misc/openldap/files/ldap-init.ldif',
      "dest": '/tmp/s3ldap/ldap-init.ldif' },
    { "src": 'salt://components/misc/openldap/files/iam-admin-access.ldif',
    "dest": '/tmp/s3ldap/iam-admin-access.ldif' },
    { "src": 'salt://components/misc/openldap/files/iam-constraints.ldif',
    "dest": '/tmp/s3ldap/iam-constraints.ldif' },
    { "src": 'salt://components/misc/openldap/files/syncprov-mod.ldif',
    "dest": '/tmp/s3ldap/syncprov-mod.ldif' },
    { "src": 'salt://components/misc/openldap/files/syncprov.ldif',
    "dest": '/tmp/s3ldap/syncprov.ldif' },
    { "src": 'salt://components/misc/openldap/files/ssl/ssl_certs.ldif',
    "dest": '/tmp/s3ldap/ssl_certs.ldif' },
    { "src": 'salt://components/misc/openldap/files/ppolicy-default.ldif',
    "dest": '/tmp/s3ldap/ppolicy-default.ldif'},
    { "src": 'salt://components/misc/openldap/files/ppolicymodule.ldif',
    "dest": '/tmp/s3ldap/ppolicymodule.ldif'},
    { "src": 'salt://components/misc/openldap/files/ppolicyoverlay.ldif',
    "dest": '/tmp/s3ldap/ppolicyoverlay.ldif'},
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
