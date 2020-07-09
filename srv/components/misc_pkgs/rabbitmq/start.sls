include:
  - components.misc_pkgs.rabbitmq.install

Start RabbitMQ service:
  service.running:
    - name: rabbitmq-server
    - enable: true
    - require:
      - Install RabbitMQ
