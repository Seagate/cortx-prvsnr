include:
  - components.misc_pkgs.rabbitmq.install
  - components.misc_pkgs.rabbitmq.start


Set RabbitMQ environment:
  file.managed:
    - name: /etc/rabbitmq/rabbitmq-env.conf
    - contents: NODENAME=rabbit@{{ grains['id'] }}
    - user: rabbitmq
    - group: rabbitmq
    - mode: 644
    - require:
      - Install RabbitMQ
    - watch_in:
      - Start RabbitMQ service

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
