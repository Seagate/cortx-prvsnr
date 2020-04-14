{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.statsd'.format(grains['id'])) %}
include:
  - components.misc_pkgs.statsd.prepare
  - components.misc_pkgs.statsd.install
  - components.misc_pkgs.statsd.config
  - components.misc_pkgs.statsd.start
  - components.misc_pkgs.statsd.sanity_check

Generate statsd checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.statsd
    - makedirs: True
    - create: True

{%- else -%}
statsd already applied:
  test.show_notification:
    - text: "statsd states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.misc_pkgs.statsd.teardown' to reprovision these states."
{% endif %}
