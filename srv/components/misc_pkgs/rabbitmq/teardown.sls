Disable plugin:
  rabbitmq_plugin.disabled:
    - name: rabbitmq_management

Remove RabbitMQ packages:
  pkg.purged:
    - name: rabbitmq-server

Remove RabbitMQ prereqs:
  pkg.purged:
    - name: erlang

Remove /var/lib/rabbitmq:
  file.absent:
    - name: /var/lib/rabbitmq

Remove plugin executable rabbitmqadmin:
  file.absent:
    - name: /usr/local/bin/rabbitmqadmin

Remove /etc/rabbitmq:
  file.absent:
    - name: /etc/rabbitmq

Delete rabbitmq checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.rabbitmq
