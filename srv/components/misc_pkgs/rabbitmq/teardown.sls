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
  - components.misc_pkgs.rabbitmq.stop

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

Remove /etc/logrotate.d/rabbitmq-server:
  file.absent:
    - name: /etc/logrotate.d/rabbitmq-server

Remove rabbitmq logs:
  file.absent:
    - name: /var/log/rabbitmq

Delete rabbitmq checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.rabbitmq
