include:
  - components.misc_pkgs.rabbitmq.start

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
    - require:
      - Start RabbitMQ service
      - Copy Erlang cookie

{% else %}

# We need this to assign master hostname
{% set master_host={"host": ""} %}
{%- for node_id in pillar['cluster']['node_list'] %}
{%- if pillar['cluster'][node_id]['is_primary'] %}
{%- if master_host.update({"host": pillar["cluster"][node_id]["hostname"].split(".")[0]}) %}
{%- endif %}
{%- endif %}
{%- endfor %}

Join rabbitmq minion to master:
  cmd.run:
    - name: |
        rabbitmqctl stop_app
        rabbitmqctl join_cluster rabbit@{{ master_host["host"] }}
        rabbitmqctl start_app
    - require:
      - Start RabbitMQ service
      - Copy Erlang cookie
{% endif %}
