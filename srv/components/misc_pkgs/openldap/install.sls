Install openldap pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients

Update to latest selinux-policy:
  pkg.installed:
    - name: selinux-policy

Install certs:
  pkg.installed:
    - sources:
      - stx-s3-certs: /opt/seagate/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
      - stx-s3-client-certs: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

Backup slapd config file:
  file.copy:
    - name: /etc/sysconfig/slapd.bak
    - source: /etc/sysconfig/slapd
    - force: True
    - preserve: True


{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) -%}
Generate Slapdpasswds:
   cmd.run:
     - name: sh /opt/seagate/eos-prvsnr/generated_configs/ldap/ldap_gen_passwd.sh
{% else -%}
{% for node_id in pillar['cluster']['node_list'] %}
{%- if pillar['cluster'][node_id]['is_primary'] %}
SCP iam-admin.ldif:
  cmd.run:
    - name: scp -r {{ pillar['cluster'][node_id]['hostname'] }}:/opt/seagate/eos-prvsnr/generated_configs/ldap/iam-admin.ldif /opt/seagate/eos-prvsnr/generated_configs/ldap/

SCP cfg_ldap.ldif:
  cmd.run:
    - name: scp -r {{ pillar['cluster'][node_id]['hostname'] }}:/opt/seagate/eos-prvsnr/generated_configs/ldap/cfg_ldap.ldif /opt/seagate/eos-prvsnr/generated_configs/ldap/
{%- endif %}
{% endfor %}
{%- endif %}


Stop slapd:
  service.dead:
    - name: slapd


{% if 'mdb' in pillar['openldap']['backend_db'] %}
Clean up old mdb ldiff file:
  file.absent:
    - name: /etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif


Copy mdb ldiff file, if not present:
  file.copy:
    - name: /etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif
    - source: /opt/seagate/eos-prvsnr/generated_configs/ldap/olcDatabase={2}mdb.ldif
    - force: True
    - user: ldap
    - group: ldap
    - watch_in:
      - service: slapd
{% endif %}


slapd:
  service.running:
    - enable: True
