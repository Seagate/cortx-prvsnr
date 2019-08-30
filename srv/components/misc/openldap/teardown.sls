{% import_yaml 'components/defaults.yaml' as defaults %}
{% set rpm_build_dir = defaults.tmp_dir + "/rpmbuild/RPMS/x86_64" %}

# Kind of slapd cleanup from here
Stop slapd:
  service.dead:
    - name: slapd

disable slapd:
  service.disabled:
    - name: slapd

set_chkconfig_off:
  cmd.run:
    - name: chkconfig slapd off
    - only_if: systemctl is-enabled slapd

Remove pkgs:
  pkg.purged:
    - pkgs:
      - openldap-servers
      - openldap-clients
      - stx-s3-client-certs
      - stx-s3-certs
    - require:
      - Stop slapd

# File cleanup operation
{% for filename in [
   '/etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif',
   '/etc/openldap/slapd.d',
   '/var/lib/ldap',
   '/etc/openldap/ldap.conf',
   '/etc/openldap/ldap.conf.bak',
   '/etc/sysconfig/slapd',
   '/opt/seagate/generated_configs/',
   '/opt/seagate/scripts/',
 ] %}
{{ filename }}:
  file.absent:
    - require:
      - pkg: Remove pkgs
{% endfor %}

# Remove directories
{% for dirname in [
    '/etc/openldap/slapd',
    '/etc/sysconfig/slapd',
    '/etc/openldap/slapd.d'
] %}
remove {{ dirname }}:
  cmd.run:
    - name: rm -rf {{ dirname }}*.*
{% endfor %}

Remove user ldap:
  user.absent:
    - name: ldap
    - purge: True
    - force: True
