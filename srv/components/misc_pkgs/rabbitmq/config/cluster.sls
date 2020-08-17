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
  - components.misc_pkgs.rabbitmq.start

Start rabbitmq app and join cluster if available:
  cmd.run:
    - name: |
        rabbitmqctl start_app
        rabbitmqctl stop_app
        {#% for node in (salt['saltutil.runner']("manage.up") | difference(grains['id'])) %#}
        {% for node in (pillar['cluster']['node_list'] | difference(grains['id'])) %}
        rabbitmqctl join_cluster rabbit@{{ node }} || true
        {% endfor %}
        rabbitmqctl start_app
        rabbitmqctl set_cluster_name rabbitmq-cluster
    - require:
      - Start RabbitMQ service
