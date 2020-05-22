include:
  - components.misc_pkgs.rabbitmq.start

Set RabbitMQ environment:
  file.managed:
    - name: /etc/rabbitmq/rabbitmq-env.conf
    - contents: NODENAME=rabbit@{{ grains['id'] }}
    - user: rabbitmq
    - group: rabbitmq
    - mode: 644

# logrotate.d config: DO NOT REMOVE
Setup logrotate policy for rabbitmq-server:
  file.managed:
  - name: /etc/logrotate.d/rabbitmq-server
  - source: salt://components/misc_pkgs/rabbitmq/files/rabbitmq-server
  - keep_source: True
  - user: root
  - group: root

Copy Erlang cookie:
  file.managed:
    - name: /var/lib/rabbitmq/.erlang.cookie
    - source: salt://components/misc_pkgs/rabbitmq/files/.erlang.cookie
    - user: rabbitmq
    - group: rabbitmq
    - mode: 0400
    - makedirs: True
    - dir_mode: 755
    - force: true
    - template: jinja
    - watch_in:
      - Start RabbitMQ service

{% if pillar["cluster"][grains["id"]]["is_primary"] -%}

Start rabbitmq app:
  cmd.run:
    - name: |
        rabbitmqctl stop_app
        rabbitmqctl start_app
        rabbitmqctl cluster_name rabbitmq-cluster
    - require:
      - Start RabbitMQ service
      - Copy Erlang cookie


{% else %}

Join rabbitmq minion to master:
  cmd.run:
    - name: |
        rabbitmqctl stop_app
        rabbitmqctl join_cluster rabbit@srvnode-1
        rabbitmqctl start_app
    - require:
      - Start RabbitMQ service
      - Copy Erlang cookie
{% endif %}
