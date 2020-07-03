{% if pillar["cluster"][grains["id"]]["is_primary"] -%}
Start rabbitmq app:
  cmd.run:
    - name: |
        rabbitmqctl stop_app
        rabbitmqctl start_app
        rabbitmqctl set_cluster_name rabbitmq-cluster
    - require:
      - Copy Erlang cookie
      - Install RabbitMQ
      - Start RabbitMQ service
{%- else %}
Join rabbitmq minion to master:
  cmd.run:
    - name: |
        rabbitmqctl stop_app
        rabbitmqctl join_cluster rabbit@srvnode-1
        rabbitmqctl start_app
    - require:
      - Copy Erlang cookie
      - Install RabbitMQ
      - Start RabbitMQ service
{%- endif %}
