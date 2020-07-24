include:
  # - components.misc_pkgs.openldap.config.base
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.start

{% if pillar['cluster']['type'] != "single" -%}
Configure unique olcserver Id:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/olcserverid.ldif && sleep 2
    - watch_in:
      - Restart slapd service

Load provider module:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_mod.ldif && sleep 2
    - require:
      - Configure unique olcserver Id
    - watch_in:
      - Restart slapd service

Push Provider ldif for config replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_config.ldif && sleep 2
    - require:
      - Load provider module
    - watch_in:
      - Restart slapd service

Push config replication:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/config.ldif && sleep 2
    - require:
      - Push Provider ldif for config replication
    - watch_in:
      - Restart slapd service

{% if "primary" in grains["roles"][0] -%}
Push provider for data replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov.ldif && sleep 2
    - require:
      - Push config replication
    - watch_in:
      - Restart slapd service

Push data replication ldif:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/data.ldif && sleep 2
    - require:
      - Push provider for data replication
    - watch_in:
      - Restart slapd service
{%- endif %}
{% endif -%}

# Validate replication configs are set using command:
# ldapsearch -w <ldappasswd> -x -D cn=admin,cn=config -b cn=config "olcSyncrepl=*"|grep olcSyncrepl: {0}rid=001
