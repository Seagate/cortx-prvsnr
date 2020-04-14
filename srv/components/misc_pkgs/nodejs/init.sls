{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.nodejs'.format(grains['id'])) %}
include:
  - .install
  - .config
  - .sanity_check

Generate nodejs checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.nodejs
    - makedirs: True
    - create: True

{%- else -%}
nodejs already applied:
  test.show_notification:
    - text: "nodejs states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.misc_pkgs.nodejs.teardown' to reprovision these states."
{% endif %}