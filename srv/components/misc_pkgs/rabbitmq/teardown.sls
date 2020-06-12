Disable plugin:
  rabbitmq_plugin.disabled:
    - name: rabbitmq_management

Remove RabbitMQ packages:
  pkg.purged:
    - name: rabbitmq-server

Remove RabbitMQ prereqs:
  pkg.purged:
    - name: erlang

Remove plugin executable rabbitmqadmin:
  file.absent:
    - name: /usr/local/bin/rabbitmqadmin

Remove /var/lib/rabbitmq:
  file.absent:
    - name: /var/lib/rabbitmq

Remove /usr/lib/rabbitmq:
  file.absent:
    - name: /usr/lib/rabbitmq

Remove /etc/rabbitmq:
  file.absent:
    - name: /etc/rabbitmq

Remove rabbitmq logs:
  file.absent:
    - name: /var/log/rabbitmq

Delete rabbitmq checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.rabbitmq
