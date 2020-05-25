# Zero dependency erlang from: https://github.com/rabbitmq/erlang-rpm/releases
Install RabbitMQ prereqs:
  pkg.installed:
    - pkgs:
      - erlang: {{ pillar ['commons']['version']['erlang'] }}

# RabbitMQ from: https://github.com/rabbitmq/rabbitmq-server/releases
Install RabbitMQ:
  pkg.installed:
    - name: rabbitmq-server
    - version: {{ pillar ['commons']['version']['rabbitmq'] }}
    - refresh: True

Enable plugin:
  rabbitmq_plugin.enabled:
    - name: rabbitmq_management
