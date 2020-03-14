{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.openldap'.format(grains['id'])) %}
include:
  - components.misc_pkgs.openldap.prepare
  - components.misc_pkgs.openldap.install
  - components.misc_pkgs.openldap.config
  - components.misc_pkgs.openldap.housekeeping
  - components.misc_pkgs.openldap.sanity_check
  - components.misc_pkgs.openldap.sanity_check

Generate openldap checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.openldap
    - makedirs: True
    - create: True
{%- else -%}
OpenLDAP already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.openldap.teardown' to reprovision these states."
{% endif %}
