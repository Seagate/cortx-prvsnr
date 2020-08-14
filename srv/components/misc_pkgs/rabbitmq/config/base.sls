#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
