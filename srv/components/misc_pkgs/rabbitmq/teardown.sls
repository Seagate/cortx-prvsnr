Remove RabbitMQ packages:
  pkg.purged:
    - name: rabbitmq-server

Remove RabbitMQ prereqs:
  pkg.purged:
    - name: erlang

Remove /var/lib/rabbitmq:
  file.absent:
    - name: /var/lib/rabbitmq

Delete rabbitmq checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.rabbitmq
