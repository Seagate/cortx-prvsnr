include:
  - components.misc_pkgs.rabbitmq.start

Start rabbitmq app and join cluster if available:
  cmd.run:
    - name: |
        rabbitmqctl start_app
        rabbitmqctl stop_app
        {% for node in (salt['saltutil.runner']("manage.up") | difference(grains['id'])) %}
        rabbitmqctl join_cluster rabbit@{{ node }} || true
        {% endfor %}
        rabbitmqctl start_app
        rabbitmqctl set_cluster_name rabbitmq-cluster
    - require:
      - Start RabbitMQ service
