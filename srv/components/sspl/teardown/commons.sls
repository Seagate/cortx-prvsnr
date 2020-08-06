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
  - components.sspl

{% set consul_service = 'hare-consul-agent-c1' if "primary" == grains['roles'] else 'hare-consul-agent-c2' %}
{% if salt['service.status'](consul_service, false) %}
Delete common config - system information to Consul:
  cmd.run:
    - name: |
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/operating_system
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/kernel_version
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/product
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/site_id
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/rack_id
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/cluster_id
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/{{ grains['id'] }}/node_id
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/syslog_host
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/syslog_port
        /opt/seagate/cortx/hare/bin/consul kv delete system_information/healthmappath
    - require:
      - Delete sspl checkpoint flag

Delete common config - rabbitmq cluster to Consul:
  cmd.run:
    - name: |
        /opt/seagate/cortx/hare/bin/consul kv delete rabbitmq/cluster_nodes
        /opt/seagate/cortx/hare/bin/consul kv delete rabbitmq/erlang_cookie
    - require:
      - Delete sspl checkpoint flag

Delete common config - BMC to Consul:
  cmd.run:
    - name: |
        /opt/seagate/cortx/hare/bin/consul kv delete bmc/srvnode-1/ip
        /opt/seagate/cortx/hare/bin/consul kv delete bmc/srvnode-1/user
        /opt/seagate/cortx/hare/bin/consul kv delete bmc/srvnode-1/secret['secret']
        /opt/seagate/cortx/hare/bin/consul kv delete bmc/srvnode-2/ip
        /opt/seagate/cortx/hare/bin/consul kv delete bmc/srvnode-2/user
        /opt/seagate/cortx/hare/bin/consul kv delete bmc/srvnode-2/secret
    - require:
      - Delete sspl checkpoint flag

Delete common config - storage enclosure to Consul:
  cmd.run:
    - name: |
        /opt/seagate/cortx/hare/bin/consul kv delete storage_enclosure/controller/primary_mc/ip
        /opt/seagate/cortx/hare/bin/consul kv delete storage_enclosure/controller/primary_mc/port
        /opt/seagate/cortx/hare/bin/consul kv delete storage_enclosure/controller/secondary_mc/ip
        /opt/seagate/cortx/hare/bin/consul kv delete storage_enclosure/controller/secondary_mc/port
        /opt/seagate/cortx/hare/bin/consul kv delete storage_enclosure/controller/user
        /opt/seagate/cortx/hare/bin/consul kv delete storage_enclosure/controller/password
    - require:
      - Delete sspl checkpoint flag

{% else %}

Delete common config:
  test.show_notification:
    - text: "Consul service not running. Nothing to do."

{% endif %}
