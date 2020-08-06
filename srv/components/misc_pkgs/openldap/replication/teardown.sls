{%- if pillar['cluster']['type'] != "single" -%}
# Cleanup
{% for filename in [
    '/opt/seagate/cortx/provisioner/generated_configs/ldap/create_replication_account.ldif',
    '/opt/seagate/cortx/provisioner/generated_configs/ldap/check_ldap_replication.sh',
    '/opt/seagate/cortx/provisioner/generated_configs/ldap/hostlist.txt'
  ]
%}
{{ filename }}_del:
  file.absent:
    - name: {{ filename }}s
{% endfor %}

Delete openldap replication checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.openldap_replication

{%- endif %}
