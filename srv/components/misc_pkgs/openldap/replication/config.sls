include:
  # - components.misc_pkgs.openldap.config.base
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.start

{% if pillar['cluster']['type'] != "single" -%}

Load provider module:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['admin']['secret']) }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_mod.ldif && sleep 2
    - watch_in:
      - Restart slapd service

Push provider for data replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['admin']['secret']) }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov.ldif && sleep 2
    - watch_in:
      - Restart slapd service

Configure openldap replication:
  cmd.run:
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -w {{ salt['lyveutil.decrypt']('openldap', pillar['openldap']['admin']['secret']) }} -f /opt/seagate/cortx/provisioner/generated_configs/ldap/replicate.ldif 
    - watch_in:
      - Restart slapd service
    - require:
      - Push provider for data replication

{% endif -%}

# Validate replication configs are set using command:
# ldapsearch -w <ldappasswd> -x -D cn=admin,cn=config -b cn=config "olcSyncrepl=*"|grep olcSyncrepl: {0}rid=001
