{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.s3server'.format(grains['id'])) %}
include:
  - components.s3server.prepare
  - components.s3server.install
  - components.s3server.config
  - components.s3server.start
  - components.s3server.housekeeping
  - components.s3server.sanity_check

Generate s3server checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.s3server
    - makedirs: True
    - create: True

{%- else -%}

S3Server already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.s3server.teardown' to reprovision these states."

{%- endif -%}
