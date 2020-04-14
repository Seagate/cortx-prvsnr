{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.firewall'.format(grains['id'])) %}
include:
  - .prepare
  - .install
  - .config
  - .sanity_check

Generate firewall checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.firewall
    - makedirs: True
    - create: True

{%- else -%}
firewall already applied:
  test.show_notification:
    - text: "firewall states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.system.firewall.teardown' to reprovision these states."
{% endif %}
