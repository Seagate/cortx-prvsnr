include:
  # - components.misc_pkgs.openldap.config.base
  - components.misc_pkgs.openldap.config.replication.prepare
  - components.misc_pkgs.openldap.start

{% if pillar['cluster']['type'] != "single" -%}
Configure openldap syncprov_mod:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_mod.ldif
    - unless:
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn=module,cn=config"
    - watch_in:
      - Start sldapd service
Configure openldap syncprov:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov.ldif
    - unless:
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "olcOverlay=syncprov,olcDatabase={2}{{ pillar['openldap']['backend_db'] }},cn=config"
    - require:
      - Configure openldap syncprov_mod
    - watch_in:
      - Start sldapd service
Configure openldap replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/replicate.ldif
    - unless:
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "cn=config"
      - ldapsearch -x -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -D "cn=admin,dc=seagate,dc=com" -H ldap:// -b "olcDatabase={2}{{ pillar['openldap']['backend_db'] }},cn=config"
    - require:
      - Configure openldap syncprov
    - watch_in:
      - Start sldapd service
{%- endif %}
