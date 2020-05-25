include:
  - components.misc_pkgs.rabbitmq.start

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
    - require_in:
      - Start RabbitMQ service

Enable plugin:
  rabbitmq_plugin.enabled:
    - name: rabbitmq_management
    - require:
      - Start RabbitMQ service

Copy plugin to /usr/local/bin:
  cmd.run:
    - name: cp $(find /var/lib/rabbitmq/ -name rabbitmqadmin) /usr/local/bin/rabbitmqadmin && chmod a+x /usr/local/bin/rabbitmqadmin
    - unless: test -f /usr/local/bin/rabbitmqadmin
