{% import_yaml 'components/defaults.yaml' as defaults %}
{% set rpm_build_dir = defaults.tmp_dir + "/rpmbuild/RPMS/x86_64" %}

# Kind of slapd cleanup from here
Stop slapd:
  service.dead:
    - name: slapd

Remove pkgs:
  pkg.purged:
    - pkgs:
      - openldap-servers
      - openldap-clients
    - require:
      - Stop slapd

# File cleanup operation
{% for filename in [
   '/etc/openldap/slapd.d/cn\=config/cn\=schema/cn\=\{1\}s3user.ldif',
   '/var/lib/ldap',
   '/etc/openldap/ldap.conf',
   '/etc/openldap/ldap.conf.bak',
   '/etc/sysconfig/slapd.bak',
   '/etc/sysconfig/slapd.repos',
   '/etc/openldap/slapd.d',
   rpm_build_dir
 ] %}
{{ filename }}:
  file.absent:
    - require:
      - pkg: Remove pkgs
{% endfor %}

Delete dir /tmp/s3ldap:
  file.absent:
    - name: /tmp/s3ldap

Remove user ldap:
  user.absent:
    - name: ldap
    - purge: True
    - force: True
