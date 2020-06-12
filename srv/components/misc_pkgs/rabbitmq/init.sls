{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.rabbitmq'.format(grains['id'])) %}
include:
  - components.misc_pkgs.rabbitmq.prepare
  - components.misc_pkgs.rabbitmq.install
  - components.misc_pkgs.rabbitmq.config
  - components.misc_pkgs.rabbitmq.start

Generate RabbitMQ checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.rabbitmq
    - makedirs: True
    - create: True
{%- else -%}
RabbitMQ already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.rabbitmq.teardown' to reprovision these states."
{% endif %}
