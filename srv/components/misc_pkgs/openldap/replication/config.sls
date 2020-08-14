include:
  # - components.misc_pkgs.openldap.config.base
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.start
  - components.misc_pkgs.openldap.sanity_check

{% if pillar['cluster']['node_list']|length > 1 -%}

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
    - name: ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/cortx/provisioner/generated_configs/ldap/replicate.ldif && sleep 10 
    - watch_in:
      - Restart slapd service
    - require:
      - Push provider for data replication
    - onchanges:
      - Verify ldap certificates valid and slapd is running

{% endif -%}


