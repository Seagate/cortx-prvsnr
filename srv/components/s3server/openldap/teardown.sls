{% import_yaml 'components/defaults.yaml' as defaults %}
{% set rpm_build_dir = defaults.tmp_dir + "/rpmbuild/RPMS/x86_64" %}

# Kind of slapd cleanup from here
stop_slapd:
  service.dead:
    - name: slapd

remove_pkgs:
  pkg.purged:
    - pkgs:
      - openldap-servers
      - openldap-clients
    - require:
      - stop_slapd

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
      - pkg: remove_pkgs
{% endfor %}

delete_tmp_s3ldap_directory:
  file.absent:
    - name: /tmp/s3ldap

Remove user ldap:
  user.absent:
    - name: ldap
    - purge: True
    - force: True
