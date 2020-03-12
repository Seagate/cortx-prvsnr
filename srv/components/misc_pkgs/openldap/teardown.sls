{% import_yaml 'components/defaults.yaml' as defaults %}
{% set rpm_build_dir = defaults.tmp_dir + "/rpmbuild/RPMS/x86_64" %}

# Kind of slapd cleanup from here
Stop slapd:
  service.dead:
    - name: slapd

disable slapd:
  service.disabled:
    - name: slapd

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
   '/var/lib/ldap',
   '/etc/sysconfig/slapd',
   '/etc/sysconfig/slapd.bak',
   '/etc/openldap/slapd.d',
   '/etc/openldap/ldap.conf',
   '/etc/openldap/ldap.conf.bak',
   '/opt/seagate/eos-prvsnr/generated_configs/ldap'
 ] %}
{{ filename }}:
  file.absent:
    - require:
      - pkg: Remove pkgs
{% endfor %}

Remove user ldap:
  user.absent:
    - name: ldap
    - purge: True
    - force: True

# Attention: Do not delete the /etc/openldap/certs dir at any cost
# Remove ldap configurations:
#   file.absent:
#     - name: /etc/openldap

Reset permissions:
  file.directory:
    - name: /etc/openldap/certs
    - user: root
    - group: root
    - recurse:
      - user
      - group

Delete openldap checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.openldap
