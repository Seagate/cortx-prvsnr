#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

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

Stop-start rabbitmq service:
  module.run:
    - service.stop:
      - rabbitmq-server
    - service.start:
      - rabbitmq-server
    - require:
      - Enable plugin rabbitmq_management

Copy plugin to /usr/local/bin:
  cmd.run:
    - name: cp $(find /var/lib/rabbitmq/ -name rabbitmqadmin) /usr/local/bin/rabbitmqadmin && chmod a+x /usr/local/bin/rabbitmqadmin
    - unless: test -f /usr/local/bin/rabbitmqadmin
    - require:
      - Stop-start rabbitmq service

Restart rabbitmq service:
  module.run:
    - service.restart:
      - rabbitmq-server
    - require:
      - Copy plugin to /usr/local/bin

# logrotate.d config: DO NOT REMOVE
Setup logrotate policy for rabbitmq-server:
  file.managed:
  - name: /etc/logrotate.d/rabbitmq-server
  - source: salt://components/misc_pkgs/rabbitmq/files/rabbitmq-server
  - keep_source: True
  - user: root
  - group: root
  - require:
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
