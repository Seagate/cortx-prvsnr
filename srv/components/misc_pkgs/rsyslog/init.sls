{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.rsyslog'.format(grains['id'])) %}
include:
  - components.misc_pkgs.rsyslog.install
  - components.misc_pkgs.rsyslog.config
  - components.misc_pkgs.rsyslog.start

Generate rsyslog checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.rsyslog
    - makedirs: True
    - create: True

{%- else -%}
rsyslog already applied:
  test.show_notification:
    - text: "rsyslog states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.misc_pkgs.rsyslog.teardown' to reprovision these states."
{% endif %}
