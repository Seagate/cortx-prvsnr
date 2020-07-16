include:
  # - components.misc_pkgs.openldap.config.base
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.start

{% if pillar['cluster']['type'] != "single" -%}
Configure unique olcserver Id:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/olcserverid.ldif
    - watch_in:
      - Start sldapd service

Load provider module:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_mod.ldif
    - require:
      - Configure unique olcserver Id
    - watch_in:
      - Start sldapd service

Push Provider ldif for config replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_config.ldif
    - require:
      - Load provider module
    - watch_in:
      - Start sldapd service

Push config replication:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/config.ldif
    - require:
      - Push Provider ldif for config replication
    - watch_in:
      - Start sldapd service

{% if "primary" in grains["roles"][0] -%}
Push provider for data replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov.ldif
    - require:
      - Push config replication
    - watch_in:
      - Start sldapd service

Push data replication ldif:
  cmd.run:
    - name: ldapmodify -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/data.ldif
    - require:
      - Push provider for data replication
    - watch_in:
      - Start sldapd service
{%- endif %}
{% endif -%}

# Validate replication configs are set using command:
# ldapsearch -w <ldappasswd> -x -D cn=admin,cn=config -b cn=config "olcSyncrepl=*"|grep olcSyncrepl: {0}rid=001
