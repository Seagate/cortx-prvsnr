{%- if pillar['cluster']['type'] != "single" -%}
{% for filename in [
    { "src": 'salt://components/misc_pkgs/openldap/files/create_replication_account.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/create_replication_account.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/check_ldap_replication.sh',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/check_ldap_replication.sh' },
  ]
%}
{{ filename.dest }}_copy:
  file.managed:
    - name: {{ filename.dest }}
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
    - template: jinja
    - require_in:
      - Replication sanity check
{% endfor %}

Hostlist file:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/ldap/hostlist.txt
    - contents: |
        {%- set node_list = (pillar['cluster']['node_list']) %}
        {{ grains['id'] -}}
        {%- for node in node_list | difference([grains['id']]) %}
        {{ node -}}
        {% endfor %}
    - user: root
    - group: root
    - require_in:
      - Replication sanity check

Replication sanity check:
  cmd.run:
    - name: sh /opt/seagate/cortx/provisioner/generated_configs/ldap/check_ldap_replication.sh -s /opt/seagate/cortx/provisioner/generated_configs/ldap/hostlist.txt -p {{ salt['lyveutil.decrypt'](pillar['openldap']['admin']['secret'],'openldap') }}
    - onlyif: test -f /opt/seagate/cortx/provisioner/generated_configs/ldap/check_ldap_replication.sh
{%- endif %}
