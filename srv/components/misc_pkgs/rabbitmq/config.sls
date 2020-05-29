include:
  - .install
  - .start

Enable plugin rabbitmq_management:
  rabbitmq_plugin.enabled:
    - name: rabbitmq_management
    - require:
      - Install RabbitMQ
    - watch_in:
      - Start RabbitMQ service

Copy plugin to /usr/local/bin:
  cmd.run:
    - name: cp $(find /var/lib/rabbitmq/ -name rabbitmqadmin) /usr/local/bin/rabbitmqadmin && chmod a+x /usr/local/bin/rabbitmqadmin
    - unless: test -f /usr/local/bin/rabbitmqadmin
    - require:
      - Enable plugin rabbitmq_management

# logrotate.d config: DO NOT REMOVE
Setup logrotate policy for rabbitmq-server:
  file.managed:
  - name: /etc/logrotate.d/rabbitmq-server
  - source: salt://components/misc_pkgs/rabbitmq/files/rabbitmq-server
  - keep_source: True
  - user: root
  - group: root
  - requrie:
    - Install RabbitMQ

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
    - require:
      - Install RabbitMQ prereqs
    - watch_in:
      - Start RabbitMQ service

{% if grains["is_primary"] -%}

Start rabbitmq app:
  cmd.run:
    - name: |
        rabbitmqctl stop_app
        rabbitmqctl start_app
    - require:
      - Copy Erlang cookie
      - Install RabbitMQ
      - Start RabbitMQ service

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
      - Copy Erlang cookie
      - Install RabbitMQ
      - Start RabbitMQ service
{% endif %}
