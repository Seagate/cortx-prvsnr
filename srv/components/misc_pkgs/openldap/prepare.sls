Remove existing certs:
  pkg.removed:
    - pkgs:
      - stx-s3-certs
      - stx-s3-client-certs

Create tmp dir:
  file.directory:
    - name: /opt/seagate/cortx/provisioner/generated_configs/ldap
    - clean: True
    - makedirs: True
    - force: True

# File copy operation on primary
{% for filename in [
    { "src": 'salt://components/misc_pkgs/openldap/files/cfg_ldap.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/cfg_ldap.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/cn={1}s3user.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/cn={1}s3user.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/iam-admin-access.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/iam-admin-access.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/iam-admin.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/iam-admin.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/iam-constraints.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/iam-constraints.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/ldap_gen_passwd.sh',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ldap_gen_passwd.sh' },
    { "src": 'salt://components/misc_pkgs/openldap/files/ldap-init.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ldap-init.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/olcDatabase={2}mdb.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/olcDatabase={2}mdb.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/ppolicy-default.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicy-default.ldif'},
    { "src": 'salt://components/misc_pkgs/openldap/files/ppolicymodule.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicymodule.ldif'},
    { "src": 'salt://components/misc_pkgs/openldap/files/ppolicyoverlay.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/ppolicyoverlay.ldif'},
    { "src": 'salt://components/misc_pkgs/openldap/files/slapdlog.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/slapdlog.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/test_data.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/test_data.ldif' },
    ]
%}
{{ filename.dest }}:
  file.managed:
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
    - template: jinja
{% endfor %}
