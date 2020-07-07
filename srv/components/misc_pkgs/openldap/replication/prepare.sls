{%- if pillar['cluster']['type'] != "single" -%}
{% for filename in [
    { "src": 'salt://components/misc_pkgs/openldap/files/syncprov.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/syncprov_mod.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/syncprov_mod.ldif' },
    { "src": 'salt://components/misc_pkgs/openldap/files/replicate.ldif',
      "dest": '/opt/seagate/cortx/provisioner/generated_configs/ldap/replicate.ldif' },
  ]
%}
{{ filename.dest }}:
  file.managed:
    - source: {{ filename.src }}
    - replace: True
    - keep_source: False
    - makedirs: True
    - template: jinja
{% endfor %}
{%- endif %}
