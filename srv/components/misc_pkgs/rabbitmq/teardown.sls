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

Disable plugin:
  rabbitmq_plugin.disabled:
    - name: rabbitmq_management

Remove RabbitMQ packages:
  pkg.purged:
    - name: rabbitmq-server

Remove RabbitMQ prereqs:
  pkg.purged:
    - name: erlang

Remove plugin executable rabbitmqadmin:
  file.absent:
    - name: /usr/local/bin/rabbitmqadmin

Remove /var/lib/rabbitmq:
  file.absent:
    - name: /var/lib/rabbitmq

Remove /usr/lib/rabbitmq:
  file.absent:
    - name: /usr/lib/rabbitmq

Remove /etc/rabbitmq:
  file.absent:
    - name: /etc/rabbitmq

Remove rabbitmq logs:
  file.absent:
    - name: /var/log/rabbitmq

Delete rabbitmq checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.rabbitmq
