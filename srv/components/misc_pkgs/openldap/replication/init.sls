{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.openldap_replication'.format(grains['id'])) %}
include:
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.replication.config
  # - components.misc_pkgs.openldap.replication.sanity_check

Generate openldap replication checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.openldap_replication
    - makedirs: True
    - create: True
{%- else -%}
OpenLDAP replication already applied:
  test.show_notification:
    - text: "OpenLDAP replication states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.openldap.teardown' to reprovision these states."
{% endif %}
